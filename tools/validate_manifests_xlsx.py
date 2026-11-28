#!/usr/bin/env python3
"""Validate / normalize / snapshot the Excel workbook (DSN-20261128-001 §9, §11).

Modes:
  default        validate structure and rules only (CI safe, no writes)
  --normalize    rewrite formatting: dark low-saturation theme (header/banding),
                 freeze header row, column widths, stats sheet rebuild (live
                 formulas), and refresh enum dropdowns (non-strict hints)
  --export-json  additionally export a JSON snapshot of the workbook
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_manifests as gm  # noqa: E402
from openpyxl import load_workbook  # noqa: E402
from openpyxl.styles import Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.workbook.defined_name import DefinedName  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = PROJECT_ROOT / "catalogs" / "manifests.xlsx"
DEFAULT_SNAPSHOT = PROJECT_ROOT / "catalogs" / "manifests-excel-snapshot.json"
MAX_COL_WIDTH = 60


# 统一标签分类体系（TSK-007 #2）：统计表为单一维护点，
# 标签分类下拉直接引用统计表清单区域，新增分类自动纳入统计。
TAG_CATEGORIES = [
    "AI应用与工具", "C++工具与桌面", "DevOps与CI/CD", "ROS与机器人",
    "Yocto与嵌入式构建", "企业级项目", "元工具与工程流程", "博客与知识发布",
    "学习与示例", "嵌入式与驱动", "待整理", "独立产品与应用", "笔记与知识库",
    "运维与监控", "Web与前端",
]

HEADER_FILL = PatternFill("solid", fgColor="37474F")  # 深蓝灰表头（低饱和暗色）
BAND_FILL_A = PatternFill("solid", fgColor="D6DEE7")  # 数据行条纹-深（偶数行）
BAND_FILL_B = PatternFill("solid", fgColor="EBEFF4")  # 数据行条纹-浅（奇数行）
TITLE_FILL = PatternFill("solid", fgColor="263238")   # 标题行


def _style_sheet(ws, band: bool = False) -> None:
    ws.freeze_panes = "A2"
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = Font(bold=True, color="FFFFFF")
    if band:
        # 逐单元格双色条纹：xlsx 行级 fill 不生效（Excel/WPS 均忽略），
        # 必须落到每个单元格；奇数行也显式着色，确保打开文件可见。
        for row_idx in range(2, ws.max_row + 1):
            fill = BAND_FILL_A if row_idx % 2 == 0 else BAND_FILL_B
            for cell in ws[row_idx]:
                cell.fill = fill


def _rebuild_stats(wb, header: list, platform_values: list) -> tuple:
    """Recreate the 统计 sheet with live formulas; return (tag_start, tag_end)."""
    if "统计" in wb.sheetnames:
        del wb["统计"]
    ws = wb.create_sheet("统计")
    attr_letter = get_column_letter(header.index("仓库属性") + 1)
    tag_letter = get_column_letter(header.index("标签分类") + 1)
    plat_letter = get_column_letter(header.index("platform") + 1)

    ws["A1"].value = "清单统计（公式随 repos 数据自动更新，勿手改公式）"
    ws["A1"].font = Font(bold=True, size=13, color="FFFFFF")
    ws["A1"].fill = TITLE_FILL
    ws["A3"].value = "仓库总数"
    ws["B3"].value = "=COUNTA(repos!$A:$A)-1"
    ws["A4"].value = "公开"
    ws["B4"].value = f'=COUNTIF(repos!${attr_letter}:${attr_letter},"公开")'
    ws["A5"].value = "私有"
    ws["B5"].value = f'=COUNTIF(repos!${attr_letter}:${attr_letter},"私有")'
    ws["A6"].value = "公开占比"
    ws["B6"].value = "=IF(B3=0,0,B4/B3)"
    ws["B6"].number_format = "0.0%"
    ws["A8"].value = "平台分布"
    ws["A8"].font = Font(bold=True)
    row = 9
    for plat in platform_values:
        ws.cell(row=row, column=1).value = plat
        ws.cell(row=row, column=2).value = f"=COUNTIF(repos!${plat_letter}:${plat_letter},A{row})"
        row += 1
    tag_head = row + 1
    ws.cell(row=tag_head, column=1).value = "标签分类体系（在此维护清单，下拉与统计自动跟随）"
    ws.cell(row=tag_head, column=1).font = Font(bold=True)
    tag_start = tag_head + 1
    for i, tag in enumerate(TAG_CATEGORIES):
        r = tag_start + i
        ws.cell(row=r, column=1).value = tag
        ws.cell(row=r, column=2).value = f"=COUNTIF(repos!${tag_letter}:${tag_letter},A{r})"
    ws.column_dimensions["A"].width = 46
    ws.column_dimensions["B"].width = 12
    return tag_start, tag_start + len(TAG_CATEGORIES) - 1


def _apply_formatting(path: Path, platform_values: list) -> None:
    wb = load_workbook(path)
    enum_columns = {
        "protocol": ["https", "git"],
        "仓库属性": ["公开", "私有"],
        "suggested_action": ["保留", "更新", "待确认", "废弃"],
    }
    if platform_values:
        enum_columns["platform"] = platform_values
    try:
        repos = wb["repos"]
        header = [c.value for c in repos[1]]
        tag_start, tag_end = _rebuild_stats(wb, header, platform_values)
        for name in ("repos", "remotes", "config", "readme"):
            ws = wb[name]
            _style_sheet(ws, band=True)
            for column_cells in ws.columns:
                width = max(
                    (len(str(c.value)) if c.value is not None else 0)
                    for c in column_cells
                )
                # CJK glyphs are roughly double-width; use a 1.9 factor cap.
                letter = get_column_letter(column_cells[0].column)
                ws.column_dimensions[letter].width = min(width * 1.9 + 2, MAX_COL_WIDTH)
        # refresh dropdowns: remove old ones on repos, re-add non-strict hints
        for dv in list(repos.data_validations.dataValidation):
            repos.data_validations.dataValidation.remove(dv)
        for column, values in enum_columns.items():
            if column not in header:
                continue
            letter = get_column_letter(header.index(column) + 1)
            dv = DataValidation(
                type="list",
                formula1='"' + ",".join(values) + '"',
                allow_blank=True,
                showErrorMessage=False,
            )
            dv.add(f"{letter}2:{letter}1000")
            repos.add_data_validation(dv)
        # 标签分类下拉：命名区域引用统计表分类清单（单一维护点）。
        # 跨表 DV 直引（统计!$A$15:$A$29）在 Excel/WPS 兼容性差，必须走命名区域。
        if "TagCategories" in wb.defined_names:
            del wb.defined_names["TagCategories"]
        wb.defined_names["TagCategories"] = DefinedName(
            "TagCategories", attr_text=f"统计!$A${tag_start}:$A${tag_end}"
        )
        tag_letter = get_column_letter(header.index("标签分类") + 1)
        dv = DataValidation(
            type="list",
            formula1="TagCategories",
            allow_blank=True,
            showErrorMessage=False,
        )
        dv.add(f"{tag_letter}2:{tag_letter}1000")
        repos.add_data_validation(dv)
        wb.save(path)
    finally:
        wb.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--normalize", action="store_true", help="rewrite formatting/dropdowns")
    parser.add_argument(
        "--export-json", nargs="?", const=str(DEFAULT_SNAPSHOT), default=None
    )
    args = parser.parse_args()

    try:
        merged = gm.load_from_excel(args.xlsx)
    except (ValueError, RuntimeError) as exc:
        print(exc)
        return 1

    if args.normalize:
        _apply_formatting(args.xlsx, sorted(merged["remotes"]))
        print(f"normalized: {args.xlsx}")

    if args.export_json:
        gm.export_snapshot(merged, Path(args.export_json))
        print(f"snapshot: {args.export_json}")

    print(
        f"OK: {len(merged['repositories'])} repositories, "
        f"{len(merged['remotes'])} platforms, owners={sorted(merged['owners'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
