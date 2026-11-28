#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pool_restore.py — 消费侧组镜像还原（manifests 适配，DSN-20261128-017-v1.0）。

用法（消费侧仅需：python3 + ctd-decoder 二进制 + JWE 私钥）：
  python3 tools/pool_restore.py \
    --image ghcr.io/zeek-zhao/manifests-pool-app:enc \
    --meta  ghcr.io/zeek-zhao/manifests-pool-app:enc-meta \
    --repo kuaidian --key ~/.secrets/jwe.key --out restore/

流程：token 交换（匿名优先，必要时 GH_PAT）→ 主镜像 manifest → 尾层 pools-manifest.json
  → -meta 镜像取 payload.bin（F-19：ctd-decoder 需 fd3 payload）→ 拉加密层 blob
  → ctd-decoder 解密 → tar 解包 → sha256 对账 manifest（RESTORE_OK / RESTORE_FAIL）。
公开镜像匿名可拉（R2 收口待 UI 切 public）；private 镜像需 GH_PAT 环境变量。
"""

import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import urllib.error
from pathlib import Path


def http_json(url, token=None, accept=(
        "application/vnd.oci.image.index.v1+json, "
        "application/vnd.oci.image.manifest.v1+json, "
        "application/vnd.docker.distribution.manifest.v2+json, "
        "application/vnd.docker.distribution.manifest.list.v2+json")):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", "Bearer %s" % token)
    req.add_header("Accept", accept)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def ghcr_token(image_repo):
    """匿名 token 优先；403（包仍 private）时回退 GH_PAT。"""
    url = "https://ghcr.io/token?service=ghcr.io&scope=repository:%s:pull" % image_repo
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.load(resp)["token"], "anonymous"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403) and os.environ.get("GH_PAT"):
            basic = base64.b64encode(("zeek-zhao:%s" % os.environ["GH_PAT"]).encode()).decode()
            req = urllib.request.Request(url, headers={"Authorization": "Basic %s" % basic})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)["token"], "pat"
        raise RuntimeError("token 交换失败（HTTP %d）：镜像未公开且未提供 GH_PAT？" % e.code)


def http_blob(url, token, dest):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer %s" % token})
    with urllib.request.urlopen(req, timeout=600) as resp, open(dest, "wb") as fh:
        shutil.copyfileobj(resp, fh, 1 << 20)


def decode_layer(decoder, key_file, enc_blob, payload_bin, out_tar, work):
    """ctd-decoder：密文走 stdin，payload 走 fd3（imgcrypt main_unix.go payloadFD=3）。"""
    keys_dir = Path(work) / "dec-keys"
    keys_dir.mkdir(exist_ok=True)
    shutil.copy(key_file, keys_dir / "key")
    fd = os.open(payload_bin, os.O_RDONLY)
    if fd != 3:
        os.dup2(fd, 3)  # 保证 payload 恰好落在 fd3
        os.close(fd)
    try:
        with open(enc_blob, "rb") as fin, open(out_tar, "wb") as fout, \
                open(str(Path(work) / "dec-err.log"), "wb") as ferr:
            r = subprocess.run(
                [decoder, "--decryption-keys-path", str(keys_dir)],
                stdin=fin, stdout=fout, stderr=ferr,
                pass_fds=(3,), cwd=str(work))
        if r.returncode != 0:
            raise RuntimeError("ctd-decoder 退出码 %d（详见 %s）"
                               % (r.returncode, Path(work) / "dec-err.log"))
    finally:
        os.close(3)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--image", required=True, help="主组镜像（ghcr.io/owner/manifests-pool-<g>:tag）")
    p.add_argument("--meta", required=True, help="meta 镜像（同 tag + -meta）")
    p.add_argument("--repo", required=True, help="要还原的仓库名（纯名）")
    p.add_argument("--layer", type=int, default=None, help="层号（缺省按 pools-manifest 查 --repo）")
    p.add_argument("--key", required=True, help="JWE 私钥路径（PKCS8，.secrets/jwe.key）")
    p.add_argument("--decoder", default="ctd-decoder", help="ctd-decoder 路径")
    p.add_argument("--out", default="restore", help="还原输出目录")
    args = p.parse_args(argv)

    if ":" not in args.image.rsplit("/", 1)[-1] or ":" not in args.meta.rsplit("/", 1)[-1]:
        raise RuntimeError("--image/--meta 必须带 tag")
    repo_path = args.image.rsplit(":", 1)[0].replace("https://", "").split("/", 1)[1]
    meta_path = args.meta.rsplit(":", 1)[0].split("/", 1)[1]
    ref = args.image.rsplit(":", 1)[1]
    meta_ref = args.meta.rsplit(":", 1)[1]

    tok, mode = ghcr_token(repo_path)
    print("token: %s" % mode)

    work = tempfile.mkdtemp(prefix="pool-restore-")
    try:
        man = http_json("https://ghcr.io/v2/%s/manifests/%s" % (repo_path, ref), tok)
        # 尾层 = pools-manifest.json（FROM scratch 尾层 COPY）
        tail = man["layers"][-1]
        tail_blob = Path(work) / "tail.tar"
        http_blob("https://ghcr.io/v2/%s/blobs/%s" % (repo_path, tail["digest"]), tok, tail_blob)
        with tarfile.open(tail_blob) as tf:
            member = [m for m in tf.getmembers() if m.name.endswith("pools-manifest.json")][0]
            pools_man = json.load(tf.extractfile(member))
        def entry_name(m):
            # 新 schema 用 name；demo 历史 schema 用 repo(owner/name)——向后兼容
            return m.get("name") or m.get("repo", "").rsplit("/", 1)[-1]

        entry = next((m for m in pools_man["repos"] if entry_name(m) == args.repo), None)
        if entry is None:
            raise RuntimeError("pools-manifest 中无仓库 %s（可用: %s）"
                               % (args.repo, [entry_name(m) for m in pools_man["repos"]]))
        layer_idx = args.layer if args.layer is not None else entry["layer_index"]
        layer = man["layers"][layer_idx]

        # meta 镜像 → payload.bin（按加密 blob digest 前 12 位命名）
        meta_tok = ghcr_token(meta_path)[0]
        meta_man = http_json("https://ghcr.io/v2/%s/manifests/%s" % (meta_path, meta_ref), meta_tok)
        if "layers" not in meta_man and "manifests" in meta_man:
            # buildx attestation index：取目标平台单 manifest 再拉一层
            cand = [m for m in meta_man["manifests"]
                    if (m.get("platform") or {}).get("architecture") not in ("unknown", None)]
            if len(cand) != 1:
                raise RuntimeError("meta 镜像 index 无法唯一定位目标 manifest（%d 候选）" % len(cand))
            meta_man = http_json("https://ghcr.io/v2/%s/manifests/%s"
                                 % (meta_path, cand[0]["digest"]), meta_tok)
        meta_layer = meta_man["layers"][0]
        meta_blob = Path(work) / "meta.tar"
        http_blob("https://ghcr.io/v2/%s/blobs/%s" % (meta_path, meta_layer["digest"]), meta_tok, meta_blob)
        with tarfile.open(meta_blob) as tf:
            for m in tf.getmembers():
                tf.extract(m, work, filter="data")
        payload_bin = Path(work) / "payloads" / ("%s.bin" % layer["digest"].split(":")[1][:12])
        if not payload_bin.exists():
            raise RuntimeError("meta 镜像缺 payload：%s（可用: %s）"
                               % (payload_bin.name, [p.name for p in (Path(work) / 'payloads').glob('*.bin')]))

        # 拉加密层 → 解密
        enc_blob = Path(work) / "enc-layer.bin"
        http_blob("https://ghcr.io/v2/%s/blobs/%s" % (repo_path, layer["digest"]), tok, enc_blob)
        dec_tar = Path(work) / "dec-layer.tar"
        decode_layer(args.decoder, args.key, enc_blob, payload_bin, dec_tar, work)
        if layer["digest"].split(":")[1][:12] not in payload_bin.name:
            pass  # 命名核对已由上方 exists 保证
        with tarfile.open(dec_tar) as tf:
            tf.extractall(args.out, filter="data")
        want = entry["sha256"]
        target = Path(args.out) / (entry.get("path") or entry.get("tar"))  # path=新 schema；tar=demo 历史版
        got = hashlib.sha256(target.read_bytes()).hexdigest()
        if got != want:
            raise RuntimeError("sha256 对账失败 %s != %s" % (got[:16], want[:16]))
        print("RESTORE_OK %s -> %s（sha256 %s… 对账一致）" % (args.repo, target, got[:16]))
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyError) as e:
        import traceback
        traceback.print_exc()
        print("FATAL: %s" % e, file=sys.stderr)
        sys.exit(2)
