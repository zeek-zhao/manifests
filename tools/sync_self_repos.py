#!/usr/bin/env python3
"""Sync self-owned repositories (name prefix == config.self_owner) into the
Excel workbook. Implements DSN-20261128-001 §8.

Per-run behavior (first table row per repo name only; extra rows such as the
obsidian multi-branch checkout are never touched):
  1. branch        <- GitHub default_branch
  2. platform      <- github (rows already on another platform are skipped, K5)
  3. description   <- GitHub API description
  4. 仓库属性    <- GitHub API visibility 原值（public/private，TSK-009 起英文值域）
  5. 仓库大小(MB) <- GitHub API size/1024（MB 保留 1 位小数，TSK-013 起单位统一 MB）
  5. protocol      <- cleared; the workbook stores the per-row preference and
                      auto rows stay protocol-less (K6)
  6. path          <- project/<repo> when empty
  + repos that disappeared upstream get their row DELETED (TSK-011: the
    authenticated /user/repos listing is the single source of truth; gitee/
    gitlab/yoctoproject rows are outside this comparison), new upstream
    repos are appended as rows with empty knowledge columns.
Knowledge columns (purpose/contents/relations/linkfiles/note/category/...)
are never overwritten. Requires GH_TOKEN or GITHUB_TOKEN.
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

try:
    from openpyxl import load_workbook
except ImportError:
    print("openpyxl is required (pip install openpyxl)")
    raise SystemExit(2)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = PROJECT_ROOT / "catalogs" / "manifests.xlsx"
API = "https://api.github.com"


def gh_get(url: str, token: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "manifests-sync-self",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_self_repos(owner: str, token: str) -> dict:
    """Authenticated /user/repos returns public AND private repos of the token
    owner; the public-only /users/{owner}/repos would falsely mark private
    repos as deleted upstream."""
    repos = {}
    page = 1
    while True:
        batch = gh_get(
            f"{API}/user/repos?per_page=100&page={page}&type=owner&sort=full_name",
            token,
        )
        if not batch:
            break
        for repo in batch:
            if repo.get("owner", {}).get("login") == owner:
                repos[repo["full_name"] + ".git"] = repo
        if len(batch) < 100:
            break
        page += 1
    return repos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--dry-run", action="store_true", help="report actions without saving")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GH_TOKEN/GITHUB_TOKEN not set")
        return 2

    wb = load_workbook(args.xlsx)
    ws = wb["repos"]
    header = [c.value for c in ws[1]]
    col = {name: header.index(name) + 1 for name in header if name}

    cfg_ws = wb["config"]
    self_owner = ""
    for row in cfg_ws.iter_rows(min_row=3, values_only=True):  # 三行结构（TSK-009）：1 表头/2 说明/3 数据
        if row and str(row[0]).strip() == "self_owner":
            self_owner = str(row[1]).strip() if row[1] else ""
            break
    if not self_owner:
        print("config.self_owner missing")
        return 2

    try:
        upstream = fetch_self_repos(self_owner, token)
    except Exception as exc:  # noqa: BLE001 - report API failures verbatim
        print(f"GitHub API error: {exc}")
        return 2

    prefix = self_owner + "/"
    seen_names = set()
    actions = []
    max_row = ws.max_row

    # 倒序遍历（TSK-011）：删行时不影响尚未遍历的行号；seen_before 仍指序号更小
    # 的行（同名首行），obsidian 双行语义保持——只处理首行。
    for r in range(max_row, 2, -1):
        name = ws.cell(row=r, column=col["name"]).value
        name = str(name).strip() if name else ""
        if not name.startswith(prefix):
            continue
        seen_names.add(name)
        seen_before = any(
            str(ws.cell(row=rr, column=col["name"]).value or "").strip() == name
            for rr in range(3, r)
        )
        if seen_before:
            continue

        platform = str(ws.cell(row=r, column=col["platform"]).value or "").strip()
        if platform and platform != "github":
            actions.append(f"row {r}: {name} 平台为 {platform}，跳过（K5）")
            continue

        repo = upstream.get(name)
        if not repo:
            # TSK-011：上游已消失 → 删除整行（认证 /user/repos 列表为唯一真源；
            # 仅影响 github 平台自有行，其他平台行在上面的 K5 分支已跳过）。
            ws.delete_rows(r)
            actions.append(f"row {r}: {name} 上游已消失，删除整行")
            continue

        row_changes = []
        default_branch = repo.get("default_branch", "")
        if default_branch and str(ws.cell(row=r, column=col["branch"]).value or "").strip() != default_branch:
            ws.cell(row=r, column=col["branch"]).value = default_branch
            row_changes.append(f"branch={default_branch}")
        if not platform:
            ws.cell(row=r, column=col["platform"]).value = "github"
            row_changes.append("platform=github")
        description = repo.get("description") or ""
        if str(ws.cell(row=r, column=col["description"]).value or "").strip() != description.strip():
            ws.cell(row=r, column=col["description"]).value = description
            row_changes.append("description=API")
        visibility = "private" if (repo.get("visibility") == "private" or repo.get("private")) else "public"
        if str(ws.cell(row=r, column=col["仓库属性"]).value or "").strip() != visibility:
            ws.cell(row=r, column=col["仓库属性"]).value = visibility
            row_changes.append(f"仓库属性={visibility}")
        api_size = repo.get("size")
        mb_value = round(api_size / 1024, 1) if api_size is not None else None
        if mb_value is not None and str(ws.cell(row=r, column=col["仓库大小(MB)"]).value or "").strip() != str(mb_value):
            ws.cell(row=r, column=col["仓库大小(MB)"]).value = mb_value
            row_changes.append(f"仓库大小(MB)={mb_value}")
        if str(ws.cell(row=r, column=col["protocol"]).value or "").strip():
            ws.cell(row=r, column=col["protocol"]).value = None
            row_changes.append("protocol 清空（K6）")
        if not str(ws.cell(row=r, column=col["path"]).value or "").strip():
            ws.cell(row=r, column=col["path"]).value = "project/" + name[len(prefix):].removesuffix(".git")
            row_changes.append("path 补全")
        if row_changes:
            actions.append(f"row {r}: {name} 更新 " + ", ".join(row_changes))

    new_names = [n for n in upstream if n not in seen_names]
    for name in sorted(new_names):
        repo = upstream[name]
        r = ws.max_row + 1
        repo_short = name[len(prefix):-len(".git")]
        defaults = {
            "name": name,
            "path": f"project/{repo_short}",
            "branch": repo.get("default_branch", ""),
            "platform": "github",
            "protocol": None,
            "description": repo.get("description") or "",
            "仓库属性": "private" if (repo.get("visibility") == "private" or repo.get("private")) else "public",
            "仓库大小(MB)": round(repo["size"] / 1024, 1) if repo.get("size") is not None else None,
        }
        for key, value in defaults.items():
            if key in col:
                ws.cell(row=r, column=col[key]).value = value
        actions.append(f"row {r}: {name} 新增（API）")

    if args.dry_run:
        print(f"[dry-run] {len(actions)} action(s):")
        for action in actions:
            print("  " + action)
        return 0

    if not actions:
        print("no changes")
        return 0
    wb.save(args.xlsx)
    print(f"saved {args.xlsx}; {len(actions)} action(s):")
    for action in actions:
        print("  " + action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
