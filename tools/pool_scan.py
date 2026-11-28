#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pool_scan.py — 组镜像池门禁扫描（manifests 适配，DSN-20261128-017-v1.0）。

三道检查（exit 0 通过 / exit 2 拦截）：
  1. ctx 原子性审计：构建目录内不得残留裸 clone 目录（红线 3：明文即删）；
  2. manifest 一致性：pools-manifest.json 条目字段齐全、encrypted 标记与快照一致口径
     （private 仓必须 encrypted=true，否则拦截——与 pool_build push 红线自检互为冗余）；
  3. 敏感文件名扫描：tar 内文件路径命中已知敏感模式（.env/id_rsa/*.pem/credentials…）即拦截。

局限（诚实声明）：tar 内容为 git 对象（zlib 压缩二进制），文本级 token 扫描对 bare tar
无效；深度内容审计依赖消费侧解密后对工作树扫描，属 pool_restore 的下游职责。
"""

import argparse
import json
import re
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pool_build import pure_name  # noqa: E402  （命名口径与构建侧一致）

SENSITIVE_NAME_RE = re.compile(
    r"(^|/)(\.env|\.env\.[^/]*|id_rsa|id_ed25519|id_ecdsa|.*\.pem$|.*\.key$|"
    r"credentials|credentials\.json|\.npmrc|\.netrc|\.git-credentials|"
    r".*secret[^/]*\.ya?ml$|secrets?\.(json|txt|ini))$", re.IGNORECASE)


def scan(args):
    ctx = Path(args.ctx)
    if not ctx.is_dir():
        raise RuntimeError("ctx 目录不存在：%s" % ctx)
    failures = []
    # 1. ctx 原子性审计
    clones = [p for p in ctx.rglob("*") if p.is_dir() and ("clone" in p.name or p.name.endswith(".git"))]
    if clones:
        failures.append("ctx 残留裸目录（红线 3）: %s" % [str(c) for c in clones])

    man_path = ctx / "pools-manifest.json"
    if not man_path.is_file():
        raise RuntimeError("缺 pools-manifest.json：%s" % man_path)
    man = json.loads(man_path.read_text(encoding="utf-8"))
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    priv_names = {pure_name(r) for r in snapshot["repositories"]
                  if str(r.get("仓库属性", "")).strip() == "private"}
    required = {"name", "layer_index", "path", "encrypted", "sha256"}
    for m in man["repos"]:
        missing = required - set(m)
        if missing:
            failures.append("manifest 条目 %s 缺字段 %s" % (m.get("name"), sorted(missing)))
        elif m["name"] in priv_names and not m["encrypted"]:
            failures.append("manifest 条目 %s 为 private 仓但 encrypted != true（快照口径）" % m["name"])

    # 3. 敏感文件名扫描
    tars = sorted((ctx / "pools" / man["group"]).glob("*.tar"))
    if not tars:
        failures.append("组 tar 缺失: %s" % (ctx / "pools" / man["group"]))
    hits = []
    for t in tars:
        with tarfile.open(t) as tf:
            for name in tf.getnames():
                if SENSITIVE_NAME_RE.search(name):
                    hits.append("%s :: %s" % (t.name, name))
    if hits:
        failures.append("敏感文件名命中:\n  " + "\n  ".join(hits[:20]))

    if failures:
        print("POOL_SCAN_FAIL")
        for f in failures:
            print("  - %s" % f)
        return 2
    print("POOL_SCAN_OK（%d 仓 / %d tar / 审计通过）" % (len(man["repos"]), len(tars)))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--ctx", required=True, help="构建目录（out/pool/<group>）")
    p.add_argument("--snapshot", default="catalogs/manifests-excel-snapshot.json")
    args = p.parse_args(argv)
    sys.exit(scan(args))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print("FATAL: %s" % e, file=sys.stderr)
        sys.exit(2)
