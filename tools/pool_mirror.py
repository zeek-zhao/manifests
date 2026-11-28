#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pool_mirror.py — 把池内 git-mirror tar 解压落位为本地 bare 镜像仓库，并生成 repo 可用的本地 manifest（M15）。

用法（消费侧；kit 套件第 5 个文件）：
  python3 tools/pool_mirror.py \
    --image ghcr.io/zeek-zhao/manifests-pool-app:run-N \
    --meta  ghcr.io/zeek-zhao/manifests-pool-app:run-N-meta \
    [--repo kuaidian | --all] \
    [--key ~/jwe.key --decoder ./pool-kit/ctd-decoder] \
    --mirror-root ~/mirror [--flat] [--fetch-base file:///home/user/mirror] \
    [--xml-out pool-manifest.xml]

流程：复用 pool_restore 拉层（private 解密/对账）→ 校验 format=git-mirror →
解压 tar 到 <mirror-root>/[<组>/]<仓>.git（原子落位）→ 校验 rev-parse == head →
生成 mirror-manifest.txt 与 repo XML（fetch 指向本地路径，--fetch-base 可配置）。
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pool_restore import fetch_repo_tar  # 下载/解密/对账唯一实现


def _get_pools_man(image):
    """仅拉取尾层 pools-manifest.json（决定目标集合与格式校验）。"""
    from pool_restore import ghcr_token, http_json, http_blob
    repo_path = image.rsplit(":", 1)[0].replace("https://", "").split("/", 1)[1]
    ref = image.rsplit(":", 1)[1]
    tok, mode = ghcr_token(repo_path)
    print("token: %s" % mode)
    man = http_json("https://ghcr.io/v2/%s/manifests/%s" % (repo_path, ref), tok)
    tail = man["layers"][-1]
    blob = Path(tempfile.mkdtemp(prefix="pool-mirror-man-")) / "tail.tar"
    try:
        http_blob("https://ghcr.io/v2/%s/blobs/%s" % (repo_path, tail["digest"]), tok, blob)
        with tarfile.open(blob) as tf:
            member = [m for m in tf.getmembers() if m.name.endswith("pools-manifest.json")][0]
            return repo_path, json.load(tf.extractfile(member))
    finally:
        shutil.rmtree(blob.parent, ignore_errors=True)


def _materialize(dec_tar, dest, head):
    """解压 mirror tar 到 dest（bare 仓库目录），临时目录+原子 rename；已存在则重建（幂等）。"""
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="pool-mirror-", dir=str(dest.parent)))
    try:
        with tarfile.open(dec_tar) as tf:
            tf.extractall(tmp, filter="data")
        # tar 顶层是 bare 内容（./HEAD ./objects ...）；处理一层包装目录的容错
        if (tmp / "HEAD").exists():
            src = tmp
        else:
            inner = [d for d in tmp.iterdir() if d.is_dir() and (d / "HEAD").exists()]
            if len(inner) != 1:
                raise RuntimeError("tar 内未找到 bare 仓库结构（HEAD 缺失）")
            src = inner[0]
        src.rename(dest)  # 同盘 rename = 原子
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    # rev-parse 校验（消费侧用 repo 必有 git；无 git 时跳过并提示）
    if shutil.which("git"):
        got = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"],
                             capture_output=True, text=True)
        if got.returncode == 0 and head and got.stdout.strip() != head:
            raise RuntimeError("%s HEAD 校验失败 %s != %s"
                               % (dest, got.stdout.strip()[:12], head[:12]))
    else:
        print("  （未检测到 git，跳过 HEAD 校验）")
    return dest


def _write_xml(repos, fetch_base, xml_out, group):
    """生成 repo 可用的本地 manifest XML；fetch 指向本地路径（--fetch-base 配置项）。"""
    fetch = fetch_base if fetch_base.endswith("/") else fetch_base + "/"
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!-- 由 pool_mirror.py 自动生成（%s；来源组：%s）；fetch 指向本地 mirror 路径 -->"
        % (datetime.now().strftime("%Y-%m-%d %H:%M"), group),
        '<manifest>',
        '  <remote name="pool" fetch="%s"/>' % fetch,
        '  <default sync-j="4"/>',
    ]
    for r in repos:
        lines.append('  <project name="%s" path="%s" revision="%s" remote="pool"/>'
                     % (r["name"], r["path_name"], r["head"] or "HEAD"))
    lines.append("</manifest>")
    Path(xml_out).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--image", required=True, help="主组镜像（ghcr.io/owner/manifests-pool-<g>:tag）")
    p.add_argument("--meta", required=True, help="meta 镜像（同 tag + -meta）")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--repo", help="单个仓库名（纯名）")
    g.add_argument("--all", action="store_true", help="落位该组全部仓库")
    p.add_argument("--key", default=None, help="JWE 私钥路径（还原加密层时必填）")
    p.add_argument("--decoder", default="ctd-decoder", help="ctd-decoder 路径")
    p.add_argument("--mirror-root", required=True, help="本地 mirror 池根目录")
    p.add_argument("--flat", action="store_true",
                   help="平铺布局 <root>/<仓>.git（缺省为 <root>/<组>/<仓>.git）")
    p.add_argument("--fetch-base", default=None,
                   help="生成 XML 的 remote fetch 前缀（缺省 file://<mirror-root 实路径>/）")
    p.add_argument("--xml-out", default=None, help="repo XML 输出路径（缺省 <root>/pool-manifest.xml）")
    args = p.parse_args(argv)

    root = Path(args.mirror_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    xml_out = args.xml_out or str(root / "pool-manifest.xml")
    fetch_base = args.fetch_base or ("file://%s/" % root)

    work = tempfile.mkdtemp(prefix="pool-mirror-work-")
    done = []
    try:
        _, pools_man = _get_pools_man(args.image)
        fmt = pools_man.get("format")
        if fmt != "git-mirror":
            raise RuntimeError("该 tag 的池产物格式为 %r（旧版 HEAD 快照），不支持 mirror 落位；"
                               "请使用 format=git-mirror 的新 tag 重跑" % fmt)
        group = pools_man.get("group", "pool")
        names = [m["name"] for m in pools_man["repos"]] if args.all else [args.repo]
        sub = root if args.flat else root / group
        quiet = args.all  # --all 时逐仓安静（token 行只打一次）
        for name in names:
            try:
                _, _, m, dec_tar = fetch_repo_tar(args.image, args.meta, name,
                                                  key=args.key, decoder=args.decoder,
                                                  work=work, quiet=quiet)
            except RuntimeError as e:
                print("MIRROR_SKIP %s：%s" % (name, str(e)[:160]))
                continue
            dest = _materialize(dec_tar, sub / ("%s.git" % name), m.get("head", ""))
            done.append({"name": name, "dest": str(dest), "head": m.get("head", "")})
            print("MIRROR_OK %s -> %s" % (name, dest))

        if not done:
            raise RuntimeError("没有仓库被落位")
        mm = (root / "mirror-manifest.txt") if args.flat else (root / ("mirror-manifest-%s.txt" % group))
        with open(mm, "w", encoding="utf-8") as fh:
            for r in done:
                fh.write("%s\t%s\t%s\n" % (r["name"], r["dest"], r["head"] or "-"))
        fb = fetch_base if args.flat else             ((fetch_base if fetch_base.endswith("/") else fetch_base + "/") + group + "/")
        xml_rows = [{"name": r["name"] + ".git", "path_name": r["name"] + ".git", "head": r["head"]} for r in done]
        _write_xml(xml_rows, fb, xml_out, group)
        print("mirror-manifest -> %s（%d 仓）" % (mm, len(done)))
        print("repo XML -> %s（remote fetch=%s；repo init -u 该文件后 repo sync --local-only 即从本地拉取）"
              % (xml_out, fb))
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
