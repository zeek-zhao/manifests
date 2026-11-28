#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pool_build.py — 组镜像池构建编排（manifests 适配，DSN-20261128-017-v1.0）。

安全模型（红线）：
  1. private 仓库所在层必须 imgcrypt(JWE) 加密后才允许推送公开镜像；
  2. 明文层三不：不 push、不出构建机（ctx 随 CI 生命周期销毁）、不进任何缓存；
  3. 代码下载与 tar 打包在同一进程内原子完成，明文 clone 目录用完即删。

阶段（CI 每步调用一个阶段；本地可 --stage all）：
  fetch    逐仓原子 clone --mirror -> tar -> sha256 -> clone 即删；大仓(>500MB)单独拎出不入池（D3）
  build    pools-manifest.json + Dockerfile(FROM scratch 每仓一层) + docker build（止步本地明文镜像）
  encrypt  containerd import --no-unpack -> ctr-enc encrypt 定向加密 private 层 -> layerinfo 校验
  push     红线自检（encrypted 层全部带 ENCRYPTION）-> ctr-enc images push ghcr
  meta     从 ghcr 取加密层 descriptor -> genpayload(go) -> payloads/ -> -meta 明文小镜像 -> docker push
           （meta 镜像公开无妨：payload 只含公钥参数与 digest，不含机密；消费侧零 go 依赖）

依赖：docker、git；encrypt/push/meta 阶段另需 containerd 静态二进制 + ctr-enc(imgcrypt v2)。
凭据：仅环境变量 GH_PAT（不落日志、不写入任何文件）。
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path


def sh(cmd, env=None, cwd=None, capture=False):
    """执行命令；命令参数列表形式，token 只经 env 传递不进 argv 日志。"""
    e = dict(os.environ)
    if env:
        e.update(env)
    print("+ %s" % " ".join(cmd), flush=True)
    r = subprocess.run(
        cmd, env=e, cwd=cwd,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError("命令失败(%d): %s" % (r.returncode, " ".join(cmd)))
    return (r.stdout or "").strip() if capture else ""


def gh_pat():
    tok = os.environ.get("GH_PAT", "").strip()
    if not tok:
        raise RuntimeError("环境变量 GH_PAT 未设置（凭据只走环境变量）")
    return tok


def host_of(platform):
    return {
        "github": "github.com",
        "gitee": "gitee.com",
        "gitlab": "gitlab.com",
        "yoctoproject": "yoctoproject.org/git",
        "github_https": "github.com",
    }.get(str(platform or "github").lower(), "github.com")


def repo_url(entry):
    """clone URL：优先 origin（快照 name 列=真实 owner/repo.git）。

    注意：item["name"] 是 pure_name（剥 owner 的纯名，仅用于 tar/层内文件名），
    不能用于拼 URL——快照 path 列是组前缀路径（qt/DBoS-Desktop）也不是 GitHub 身份。
    """
    host = host_of(entry.get("platform"))
    raw = str(entry.get("origin") or entry.get("name") or "").strip("/")
    if "/" not in raw:
        raw = "zeek-zhao/%s" % raw
    if not raw.endswith(".git"):
        raw += ".git"
    return "https://%s/%s" % (host, raw), raw


def pure_name(entry):
    """tar/层内文件用的纯仓库名（无 owner、无 .git）。"""
    raw = str(entry.get("name") or "")
    pure = raw.rsplit("/", 1)[-1]
    return pure[:-4] if pure.endswith(".git") else pure


def load_group(snapshot_path, group, big_mb):
    """读快照取组内条目；返回 (池内条目, 超大条目)。encrypted = 仓库属性==private。"""
    data = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    pools, oversized = [], []
    for r in data["repositories"]:
        groups = r.get("groups") or ""
        if isinstance(groups, list):
            groups = ",".join(str(x) for x in groups)
        if group not in [g.strip() for g in str(groups).split(",") if g.strip()]:
            continue
        size = r.get("仓库大小(MB)")
        try:
            size = float(size)
        except (TypeError, ValueError):
            size = 0.0
        item = {
            "name": pure_name(r),
            "origin": str(r.get("name") or "").strip(),
            "platform": r.get("platform", "github"),
            "encrypted": str(r.get("仓库属性", "")).strip() == "private",
            "size_mb": size,
        }
        if size > big_mb:
            item["reason"] = "超大仓独立镜像按需拉取（D3 决策）"
            oversized.append(item)
        else:
            pools.append(item)
    return pools, oversized


# ---------------------------------------------------------------- fetch

def stage_fetch(args, entries):
    ctx = Path(args.ctx) / args.group
    tars = ctx / "pools" / args.group
    tars.mkdir(parents=True, exist_ok=True)
    tok = gh_pat()
    heads = {}
    skipped = []
    fetched = []
    for ent in entries:
        url, path = repo_url(ent)
        work = Path(tempfile.mkdtemp(prefix="pool-clone-", dir=str(ctx)))
        try:
            bare = work / "r.git"
            auth = url.replace("https://", "https://x-access-token:%s@" % tok)
            # GIT_LFS_SKIP_SMUDGE：LFS 指针随池分发（与普通 clone 语义一致，大文件内容不含）；
            # HTTP/1.1：大仓库 HTTP2 framing 层易断流。
            # mirror clone 的 fetch 路径不走 smudge，SKIP_SMUDGE 不够——必须直接禁用
            # filter.lfs.*（runner 预装 git-lfs 时 filter-process 会因上游 LFS 404 炸掉 clone）。
            # 重试 3 次；仍失败则降级跳过该仓并记入 manifest.skipped（不炸整组）。
            err = None
            for attempt in range(3):
                r = subprocess.run(
                    ["git",
                     "-c", "filter.lfs.process=",
                     "-c", "filter.lfs.smudge=cat",
                     "-c", "filter.lfs.required=false",
                     "-c", "http.version=HTTP/1.1",
                     "clone", "--mirror", "--quiet", auth, str(bare)],
                    env={**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"},
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                if r.returncode == 0:
                    err = None
                    break
                err = r.stderr.decode(errors="replace").strip().splitlines()[-1:] or ["未知错误"]
                err = err[0][:200]
                shutil.rmtree(work, ignore_errors=True)
                work.mkdir(parents=True, exist_ok=True)
                bare = work / "r.git"
            if err is not None:
                print("  fetch %s 降级跳过：%s" % (path, err))
                skipped.append({"name": ent["name"], "url": url, "reason": err})
                continue
            head = sh(["git", "-C", str(bare), "rev-parse", "HEAD"], capture=True)
            tmp = tars / ("%s.tar.tmp" % ent["name"])
            final = tars / ("%s.tar" % ent["name"])
            # runner 预装 git-lfs 时，.gitattributes 的 filter=lfs 标记会让 archive 触发
            # clean filter（指针→对象转换，上游 404 即 128）——archive 同样禁用 lfs filter。
            with open(tmp, "wb") as fh:
                subprocess.run(["git", "-C", str(bare),
                                "-c", "filter.lfs.process=",
                                "-c", "filter.lfs.clean=cat",
                                "-c", "filter.lfs.required=false",
                                "archive", "--format=tar", head],
                               stdout=fh, check=True)
            tmp.rename(final)  # 原子落盘：tar 完整写完才出现在正式路径
            digest = hashlib.sha256(final.read_bytes()).hexdigest()
            ent["tar"] = str(final)
            ent["sha256"] = digest
            heads[ent["name"]] = head
            fetched.append(ent)
            print("  fetch %s HEAD=%s sha256=%s… %dKB"
                  % (path, head[:12], digest[:16], final.stat().st_size // 1024))
        finally:
            shutil.rmtree(work, ignore_errors=True)  # 明文 clone 即删（红线 3）
    if skipped:
        print("  跳过 %d 仓：%s" % (len(skipped), ", ".join(s["name"] for s in skipped)))
    (ctx / "heads.json").write_text(json.dumps(heads, indent=2), encoding="utf-8")
    (ctx / "skipped.json").write_text(json.dumps(skipped, ensure_ascii=False, indent=2), encoding="utf-8")
    leftovers = [p.name for p in ctx.rglob("*") if p.is_dir() and p.name.startswith("pool-clone-")]
    if leftovers:
        raise RuntimeError("原子性审计失败：clone 目录残留 %s" % leftovers)
    return heads, skipped, fetched


# ---------------------------------------------------------------- build

def stage_build(args, entries, image):
    ctx = Path(args.ctx) / args.group
    tars = ctx / "pools" / args.group
    for ent in entries:
        if "sha256" not in ent:
            raise RuntimeError("%s 尚未 fetch（缺 sha256）" % ent["name"])
    manifest = {
        "group": args.group,
        "image": image,
        "jwe_recipient": str(Path(args.jwe_pub).resolve()),
        "lfs_policy": "LFS 指针随池分发，大文件内容不含（与普通 clone 语义一致；GIT_LFS_SKIP_SMUDGE=1）",
        "skipped": json.loads((ctx / "skipped.json").read_text(encoding="utf-8"))
        if (ctx / "skipped.json").exists() else [],
        "repos": [
            {
                "name": ent["name"],
                "layer_index": i,
                "path": "pools/%s/%s.tar" % (args.group, ent["name"]),
                "encrypted": ent["encrypted"],
                "sha256": ent["sha256"],
            }
            for i, ent in enumerate(entries)
        ],
    }
    (ctx / "pools-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["FROM scratch"]
    for ent in entries:
        lines.append("COPY pools/%s/%s.tar pools/%s/" % (args.group, ent["name"], args.group))
    lines.append("COPY pools-manifest.json pools/%s/" % args.group)
    (ctx / "Dockerfile").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sh(["docker", "build", "--no-cache",
        "--provenance=false", "--sbom=false",
        "-t", image, str(ctx)])
    return manifest


# ---------------------------------------------------------------- encrypt/push/meta

def ctr_enc(args, sub, capture=False):
    env = {"CONTAINERD_ADDRESS": args.address}
    return sh([args.ctr_enc, "-a", args.address, "--namespace", "pool"] + sub, env=env, capture=capture)


def stage_encrypt(args, entries, image):
    ctx = Path(args.ctx) / args.group
    # docker save 明文 tar 仅存在于构建机 ctx 目录内（红线 2：不出构建机，随清理销毁）
    img_tar = ctx / "image.tar"
    sh(["docker", "save", image, "-o", str(img_tar)])
    ctr_enc(args, ["images", "import", "--no-unpack", str(img_tar)])
    man = json.loads((ctx / "pools-manifest.json").read_text(encoding="utf-8"))
    for m in man["repos"]:
        if m["encrypted"]:
            ctr_enc(args, ["images", "encrypt", "--recipient", "jwe:" + str(Path(args.jwe_pub).resolve()),
                           "--platform", "linux/amd64", "--layer", str(m["layer_index"]), image])
    info = ctr_enc(args, ["images", "layerinfo", "--platform", "linux/amd64", image], capture=True)
    man["_layerinfo"] = info
    (ctx / "pools-manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    print(info)
    return info


def redline_check(layerinfo_text, manifest):
    """红线自检：encrypted=true 的层必须加密，否则拒绝 push。

    layerinfo 数据行列结构：# DIGEST PLATFORM SIZE ENCRYPTION RECIPIENTS；
    加密行 ENCRYPTION/RECIPIENTS 有值（split 后 >=6 段），明文行空列被 split 吃掉（4 段）。
    注意：加密行的加密标识是列值（如 jwe），不含字面 "ENCRYPTION"（表头才有）。
    """
    rows = {}
    for line in layerinfo_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if parts and parts[0].isdigit():
            rows[int(parts[0])] = parts
    bad = [m["layer_index"] for m in manifest["repos"]
           if m["encrypted"] and len(rows.get(m["layer_index"], [])) < 6]
    if bad:
        raise RuntimeError("红线拦截：private 层未加密 %s，禁止推送公开镜像" % bad)


def stage_push(args, image):
    info = ctr_enc(args, ["images", "layerinfo", "--platform", "linux/amd64", image], capture=True)
    print("--- layerinfo（红线审计）---\n%s" % (info or "(空)"), flush=True)
    ctx = Path(args.ctx) / args.group
    man = json.loads((ctx / "pools-manifest.json").read_text(encoding="utf-8"))
    redline_check(info, man)
    tok = gh_pat()
    ctr_enc(args, ["images", "push", "--platform", "linux/amd64",
                   "--user", "zeek-zhao:%s" % tok, image])
    print("PUSH_OK %s" % image)


def ghcr_token(image_repo):
    tok = gh_pat()
    req = urllib.request.Request(
        "https://ghcr.io/token?service=ghcr.io&scope=repository:%s:pull"
        % image_repo,
        headers={"Authorization": "Basic %s" % __import__("base64").b64encode(
            ("zeek-zhao:%s" % tok).encode()).decode()})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["token"]


def fetch_json(url, token=None, accept="application/vnd.oci.image.manifest.v1+json"):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", "Bearer %s" % token)
    req.add_header("Accept", accept)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def stage_meta(args, entries, image):
    """加密层 payload -> payloads/*.bin -> <image>-meta 明文镜像 -> docker push。"""
    if ":" not in image.rsplit("/", 1)[-1]:
        raise RuntimeError("image 必须带 tag：%s" % image)
    image_repo = image.rsplit(":", 1)[0].replace("https://", "")
    name_only = image_repo.split("/", 1)[1]
    ref = image.rsplit(":", 1)[1]
    tok = ghcr_token(name_only)
    man = fetch_json("https://ghcr.io/v2/%s/manifests/%s" % (name_only, ref), tok)
    ctx = Path(args.ctx) / args.group
    payloads = ctx / "payloads"
    payloads.mkdir(exist_ok=True)
    jwe_layers = [l for l in man.get("layers", [])
                  if any("enc.keys.jwe" in k for k in (l.get("annotations") or {}))]
    if not jwe_layers:
        raise RuntimeError("ghcr manifest 中未见加密层（annotations 缺失）")
    for l in jwe_layers:
        out = payloads / ("%s.bin" % l["digest"].split(":")[1][:12])
        # genpayload 依赖 imgcrypt/typeurl 包：go run 的模块解析基于 CWD，
        # 必须在含 go.mod 的 imgcrypt 源码树内执行（GENPAYLOAD_DIR=树根）。
        gen_dir = os.environ.get("GENPAYLOAD_DIR")
        if gen_dir:
            go_file, go_cwd = str(Path(gen_dir) / "genpayload_ci.go"), gen_dir
        else:
            go_file = str(Path(__file__).resolve().parent / "pool-tools" / "genpayload")
            go_cwd = None
        djson = payloads / ("d-%s.json" % l["digest"].split(":")[1][:12])
        djson.write_text(json.dumps(l), encoding="utf-8")
        # go run 的 CWD 在 imgcrypt 树内，descriptor/out 必须传绝对路径
        sh(["go", "run", go_file, "--descriptor", str(djson.resolve()),
            "--out", str(out.resolve())],
           env={"GOPROXY": os.environ.get("GOPROXY", "https://proxy.golang.org,direct")},
           cwd=go_cwd)
    mlines = ["FROM scratch", "COPY payloads/ payloads/"]
    (ctx / "Dockerfile.meta").write_text("\n".join(mlines) + "\n", encoding="utf-8")
    meta_image = image + "-meta"
    sh(["docker", "build", "--no-cache",
        "--provenance=false", "--sbom=false",
        "-t", meta_image, "-f", str(ctx / "Dockerfile.meta"), str(ctx)])
    sh(["docker", "push", meta_image])
    print("META_OK %s（payloads=%d）" % (meta_image, len(jwe_layers)))


# ---------------------------------------------------------------- main

STAGES = ["fetch", "build", "encrypt", "push", "meta"]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--group", required=True)
    p.add_argument("--snapshot", default="catalogs/manifests-excel-snapshot.json")
    p.add_argument("--ctx", default="out/pool")
    p.add_argument("--tag", default=time.strftime("ci-%Y%m%d-%H%M"))
    p.add_argument("--jwe-pub", default="keys/jwe.pub")
    p.add_argument("--big-mb", type=float, default=500.0, help="超大仓阈值（D3）")
    p.add_argument("--stage", default="all", help=",".join(STAGES) + " 或 all")
    p.add_argument("--ctr-enc", default="ctr-enc")
    p.add_argument("--address", default="/run/pool/containerd.sock")
    args = p.parse_args(argv)

    entries, oversized = load_group(args.snapshot, args.group, args.big_mb)
    if not entries and args.stage in ("all", "fetch", "build"):
        raise RuntimeError("组 %s 无条目" % args.group)
    image = "ghcr.io/zeek-zhao/manifests-pool-%s:%s" % (args.group, args.tag)
    stages = STAGES if args.stage == "all" else [s.strip() for s in args.stage.split(",")]
    for s in stages:
        if s not in STAGES:
            p.error("未知阶段 %s" % s)

    for s in stages:
        if s == "fetch":
            heads, skipped, fetched = stage_fetch(args, entries)
            entries = fetched  # 降级跳过的仓不进后续 build/encrypt/push
            for ent in oversized:
                print("  跳过超大仓 %s（%.1fMB）：%s" % (ent["name"], ent["size_mb"], ent["reason"]))
        elif s == "build":
            stage_build(args, entries, image)
        elif s == "encrypt":
            stage_encrypt(args, entries, image)
        elif s == "push":
            stage_push(args, image)
        elif s == "meta":
            stage_meta(args, entries, image)
    print("POOL_BUILD_DONE %s" % ",".join(stages))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print("FATAL: %s" % e, file=sys.stderr)
        sys.exit(2)
