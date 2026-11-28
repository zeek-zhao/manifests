#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stats_report.py - TSK-20261128-010 D-7/D-8.

Dynamically pull GitHub API repository metrics (stars/forks/size/pushed_at), write them into
the new sheet "动态统计" in manifests.xlsx, and generate 4 native charts (openpyxl):
  1. 标签分类分布条形图   2. 平台分布饼图
  3. size Top15 条形图    4. public/private 饼图

Table structure follows the repository convention: row 1 = header, row 2 = explanation row,
row 3+ = data (131 rows all listed; metrics for non-github platforms left empty).
This sheet is fully owned by this tool and rebuilt idempotently; --normalize does not touch it.

Only github-platform rows call the GitHub API (gitee/gitlab/yoctoproject have no equivalent
public metrics API, leave empty; see REF-20261128-006 §5). Token taken from GH_TOKEN /
GITHUB_TOKEN; without a token, private repositories return 404 and metrics are left empty.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone  # noqa: F401  (reserved for report extensions)
from pathlib import Path

import openpyxl
from openpyxl.chart import BarChart, PieChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_manifests as gm  # noqa: E402  (load_from_excel reuse)

DEFAULT_XLSX = Path("catalogs/manifests.xlsx")
SHEET = "动态统计"
DATA_START = 3
HEADERS = ["name", "platform", "标签分类", "仓库属性", "stars", "forks", "size_MB", "pushed_at"]
DOCS = {
    "name": "仓库全名 owner/repo.git（与 repos 表一致）",
    "platform": "托管平台（github 行才有 API 指标，其余平台留空）",
    "标签分类": "引自 repos 表标签分类（管理统计维度）",
    "仓库属性": "public/private（引自 repos 表）",
    "stars": "GitHub API stargazers_count（实时拉取）",
    "forks": "GitHub API forks_count（实时拉取）",
    "size_MB": "GitHub API size/1024（MB，实时拉取）",
    "pushed_at": "GitHub API pushed_at（UTC 日期部分）",
}
# 辅助区（图表数据源，避免图表跨 sheet 引用的兼容性问题）
AUX_TAG_HEAD = 2      # J2:J15 标签计数，I2:I15 标签名
AUX_PLAT_HEAD = 19    # J19:J22 平台计数
AUX_VIS_ROW = 26      # I26/J26 public、I27/J27 private
AUX_TOP_HEAD = 30     # J31:J45 Top15 size，I31:I45 仓库名
HDR_FILL = PatternFill("solid", fgColor="37474F")
DOCS_FILL = PatternFill("solid", fgColor="E3E9F0")
BAND_FILL = PatternFill("solid", fgColor="D6DEE7")


def _gh_headers(token: str) -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "manifests-stats"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def fetch_metrics(names: list[str], token: str, sleep: float = 0.15) -> dict:
    """Return {full_name_without_.git: {stars, forks, size, pushed_at}}; missing → absent."""
    out: dict = {}
    for full in names:
        url = f"https://api.github.com/repos/{full}"
        req = urllib.request.Request(url, headers=_gh_headers(token))
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                d = json.load(resp)
            out[full] = {
                "stars": int(d.get("stargazers_count") or 0),
                "forks": int(d.get("forks_count") or 0),
                "size": int(d.get("size") or 0),
                "pushed_at": (d.get("pushed_at") or "")[:10],
            }
        except Exception as exc:  # noqa: BLE001  (404 private/deleted → leave empty)
            print(f"  [warn] {full}: {exc}")
        time.sleep(sleep)
    return out


def build_sheet(wb, repos: list[dict], metrics: dict) -> None:
    if SHEET in wb.sheetnames:
        del wb[SHEET]
    ws = wb.create_sheet(SHEET)
    for c, h in enumerate(HEADERS, 1):
        cell = ws.cell(1, c)
        cell.value = h
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = HDR_FILL
    for c, h in enumerate(HEADERS, 1):
        cell = ws.cell(2, c)
        cell.value = DOCS[h]
        cell.font = Font(italic=True, size=9, color="546E7A")
        cell.fill = DOCS_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center")

    for i, r in enumerate(repos):
        row = DATA_START + i
        full = r["name"]
        key = full[:-4] if full.endswith(".git") else full
        m = metrics.get(key, {})
        vals = [
            full,
            r.get("platform") or "",
            r.get("标签分类") or "",
            r.get("仓库属性") or "",
            m.get("stars"),
            m.get("forks"),
            round((m.get("size") or 0) / 1024, 1),
            m.get("pushed_at"),
        ]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row, c)
            if v is not None:
                cell.value = v
            if (row - DATA_START) % 2 == 0:
                cell.fill = BAND_FILL
    ws.freeze_panes = "A3"
    # 表头筛选（TSK-014）：与四表一致，AutoFilter 自表头行 1 覆盖数据区。
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}{row - 1}"

    # ---- 辅助区（公式随数据区自动更新）----
    gh_rows = DATA_START + len(repos) - 1
    stat = wb["统计"]
    tag_start = None
    for r in range(1, stat.max_row + 1):
        if stat.cell(r, 1).value == "标签分类体系（在此维护清单，下拉与统计自动跟随）":
            tag_start = r + 1
            break
    labels = []
    if tag_start:
        r = tag_start
        while stat.cell(r, 1).value:
            labels.append(stat.cell(r, 1).value)
            r += 1
    ws.cell(1, 10).value = "标签分布（图表数据源，勿手改）"
    for i, lab in enumerate(labels):
        ws.cell(AUX_TAG_HEAD + i, 9).value = lab
        ws.cell(AUX_TAG_HEAD + i, 10).value = f"=COUNTIF($C${DATA_START}:$C${gh_rows},I{AUX_TAG_HEAD + i})"
    platforms = sorted({r.get("platform") or "" for r in repos})
    ws.cell(18, 10).value = "平台分布（图表数据源，勿手改）"
    for i, p in enumerate(platforms):
        ws.cell(AUX_PLAT_HEAD + i, 9).value = p
        ws.cell(AUX_PLAT_HEAD + i, 10).value = f"=COUNTIF($B${DATA_START}:$B${gh_rows},I{AUX_PLAT_HEAD + i})"
    ws.cell(25, 10).value = "仓库属性（图表数据源，勿手改）"
    for i, v in enumerate(("public", "private")):
        ws.cell(AUX_VIS_ROW + i, 9).value = v
        ws.cell(AUX_VIS_ROW + i, 10).value = f"=COUNTIF($D${DATA_START}:$D${gh_rows},I{AUX_VIS_ROW + i})"

    # size Top15（Python 侧排序写入静态值；API 刷新时随数据区重算）
    sized = sorted(
        ((r["name"],
          (metrics.get(r["name"][:-4] if r["name"].endswith(".git") else r["name"]) or {}).get("size") or 0)
         for r in repos),
        key=lambda x: -x[1])[:15]
    ws.cell(AUX_TOP_HEAD, 10).value = "size Top15（MB，图表数据源）"
    for i, (n, s) in enumerate(sized):
        ws.cell(AUX_TOP_HEAD + 1 + i, 9).value = n.split("/")[-1]
        ws.cell(AUX_TOP_HEAD + 1 + i, 10).value = round(s / 1024, 1)

    _add_charts(ws, len(labels), len(platforms), len(sized))
    _auto_width(ws)


def _add_charts(ws, n_labels: int, n_plats: int, n_top: int) -> None:
    bar = BarChart()
    bar.type, bar.style, bar.title = "col", 10, "标签分类分布"
    bar.add_data(Reference(ws, min_col=10, min_row=AUX_TAG_HEAD, max_row=AUX_TAG_HEAD + n_labels - 1), titles_from_data=False)
    bar.set_categories(Reference(ws, min_col=9, min_row=AUX_TAG_HEAD, max_row=AUX_TAG_HEAD + n_labels - 1))
    bar.height, bar.width, bar.legend = 8, 18, None
    ws.add_chart(bar, "M2")

    pie = PieChart()
    pie.title = "平台分布"
    pie.add_data(Reference(ws, min_col=10, min_row=AUX_PLAT_HEAD, max_row=AUX_PLAT_HEAD + n_plats - 1), titles_from_data=False)
    pie.set_categories(Reference(ws, min_col=9, min_row=AUX_PLAT_HEAD, max_row=AUX_PLAT_HEAD + n_plats - 1))
    pie.height, pie.width = 8, 12
    ws.add_chart(pie, "M20")

    top = BarChart()
    top.type, top.style, top.title = "bar", 10, "仓库大小 Top15（MB）"
    top.add_data(Reference(ws, min_col=10, min_row=AUX_TOP_HEAD + 1, max_row=AUX_TOP_HEAD + n_top), titles_from_data=False)
    top.set_categories(Reference(ws, min_col=9, min_row=AUX_TOP_HEAD + 1, max_row=AUX_TOP_HEAD + n_top))
    top.height, top.width, top.legend = 10, 18, None
    ws.add_chart(top, "M38")

    vis = PieChart()
    vis.title = "public / private"
    vis.add_data(Reference(ws, min_col=10, min_row=AUX_VIS_ROW, max_row=AUX_VIS_ROW + 1), titles_from_data=False)
    vis.set_categories(Reference(ws, min_col=9, min_row=AUX_VIS_ROW, max_row=AUX_VIS_ROW + 1))
    vis.height, vis.width = 8, 12
    ws.add_chart(vis, "M60")


def _auto_width(ws) -> None:
    for col in range(1, len(HEADERS) + 1):
        best = 0
        for r in (1, 2):
            v = ws.cell(r, col).value or ""
            best = max(best, sum(2 if ord(ch) > 0x2E7F else 1 for ch in str(v)))
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = min(best + 2, 30)


def main() -> int:
    ap = argparse.ArgumentParser(description="Dynamically pull GitHub repository metrics and generate statistics charts into the 动态统计 sheet")
    ap.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX, help="Workbook path")
    args = ap.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    ctx = gm.load_from_excel(str(args.xlsx))
    repos = ctx["repositories"]
    gh_names = []
    for r in repos:
        if r.get("platform") == "github":
            n = r["name"]
            gh_names.append(n[:-4] if n.endswith(".git") else n)
    print(f"Pulling metrics for {len(gh_names)} github repos (token: {'yes' if token else 'NO'}) ...")
    metrics = fetch_metrics(gh_names, token)
    wb = openpyxl.load_workbook(args.xlsx)
    build_sheet(wb, repos, metrics)
    wb.save(args.xlsx)
    got = len(metrics)
    print(f"动态统计 sheet rebuilt: {len(repos)} rows, {got}/{len(gh_names)} github repos with metrics.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
