#!/usr/bin/env python3
"""autofill_repos.py - 新仓库自动填充（TSK-20261128-015 #4）

对 manifests.xlsx repos 表 github 平台的行，扫描空字段并用 GitHub API 自动填充：
  branch <- default_branch; platform <- github（空才补）;
  description <- API description（空才补，自有行照 API、外部行同样可填）;
  仓库属性 <- private/public; 仓库大小(MB) <- round(size/1024, 1);
  language <- API 主语言映射（c/c++、nodejs 等既有 slug 体系，空 -> mixed）。
知识列（purpose/contents/relations/标签分类/suggested_action/note）**永不自动填写**，
留人工/AI 辅助（当前无 LLM 凭证，规则推断不落盘）。

用法：
  python3 tools/autofill_repos.py [--repo owner/repo.git] [--dry-run]
  （GitHub 认证取 GH_TOKEN / GITHUB_TOKEN；无 token 时依赖匿名限额并可能 403）

原子性：仅更新存在且为空的单元格；任何写盘前打印全部拟议变更。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

from openpyxl import load_workbook

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = REPO_ROOT / "catalogs" / "manifests.xlsx"
DATA_START_ROW = 3
API = "https://api.github.com/repos/{}"
LANG_MAP = {"c++": "c/c++", "javascript": "nodejs", "typescript": "nodejs"}


def _token() -> str:
    import os
    return os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""


def _fetch(full_name: str, token: str) -> dict | None:
    req = urllib.request.Request(API.format(full_name))
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "manifests-autofill")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except Exception as exc:  # 404/403/网络
        print(f"  !! {full_name}: {exc}")
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="仅处理该行（owner/repo.git）")
    ap.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    token = _token()
    if not token:
        print("WARN: 无 GH_TOKEN/GITHUB_TOKEN，匿名限额（60/h）大概率不足")
    wb = load_workbook(args.xlsx)
    ws = wb["repos"]
    header = {str(ws.cell(row=1, column=c).value or "").strip(): c
              for c in range(1, ws.max_column + 1)}
    FILL = ["branch", "platform", "description", "仓库属性", "仓库大小(MB)", "language"]
    actions: list[tuple[int, str, str, object]] = []
    cache: dict[str, dict | None] = {}

    for r in range(DATA_START_ROW, ws.max_row + 1):
        name = str(ws.cell(row=r, column=1).value or "").strip()
        if not name or name == "合计":
            if name == "合计":
                break
            continue
        if args.repo and name != args.repo:
            continue
        platform = str(ws.cell(row=r, column=header["platform"]).value or "").strip()
        if platform != "github":
            continue
        empties = [f for f in FILL
                   if not str(ws.cell(row=r, column=header[f]).value or "").strip()]
        if not empties:
            continue
        full = name[:-4] if name.endswith(".git") else name
        if full not in cache:
            cache[full] = _fetch(full, token)
            time.sleep(0.2)
        m = cache[full]
        if not m:
            continue
        if "branch" in empties and m.get("default_branch"):
            actions.append((r, name, "branch", m["default_branch"]))
        if "platform" in empties:
            actions.append((r, name, "platform", "github"))
        if "description" in empties and m.get("description"):
            actions.append((r, name, "description", m["description"]))
        if "仓库属性" in empties:
            vis = "private" if (m.get("visibility") == "private" or m.get("private")) else "public"
            actions.append((r, name, "仓库属性", vis))
        if "仓库大小(MB)" in empties and m.get("size") is not None:
            actions.append((r, name, "仓库大小(MB)", round(m["size"] / 1024, 1)))
        if "language" in empties:
            lang = (m.get("language") or "").strip()
            mapped = LANG_MAP.get(lang.lower(), lang.lower()) if lang else "mixed"
            actions.append((r, name, "language", mapped))

    if not actions:
        print("无需填充：目标行无空字段（或 API 全部不可达）")
        return 0
    for r, name, field, val in actions:
        print(f"  行{r} {name}: {field} <- {val}")
    if args.dry_run:
        print(f"dry-run：共 {len(actions)} 项，未写盘")
        return 0
    for r, _, field, val in actions:
        ws.cell(row=r, column=header[field]).value = val
    wb.save(args.xlsx)
    print(f"已写 {len(actions)} 项 -> {args.xlsx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
