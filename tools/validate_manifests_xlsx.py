#!/usr/bin/env python3
"""Validate / normalize / snapshot the Excel workbook (DSN-20261128-001 §9, §11).

Modes:
  default        validate structure and rules only (CI safe, no writes)
  --normalize    rewrite formatting: three-row layout (header / column docs /
                 data, TSK-009), dark low-saturation theme with tight column
                 widths and wrap_text, stats sheet rebuild (live formulas),
                 and refresh enum dropdowns (inline list + named range)
  --export-json  additionally export a JSON snapshot of the workbook
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_manifests as gm  # noqa: E402
from openpyxl import load_workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.workbook.defined_name import DefinedName  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = PROJECT_ROOT / "catalogs" / "manifests.xlsx"
DEFAULT_SNAPSHOT = PROJECT_ROOT / "catalogs" / "manifests-excel-snapshot.json"
MAX_COL_WIDTH = 28          # 紧凑列宽上限（TSK-009 D-5）
DOCS_ROW = 2                # 列说明行
DATA_START_ROW = 3          # 与 gm.DATA_START_ROW 一致

# 统一标签分类体系（TSK-007 #2）：统计表为单一维护点，
# 下拉同时生成内联枚举（打开文件即生效）与命名区域（文档化引用）。
TAG_CATEGORIES = [
    "AI应用与工具", "C++工具与桌面", "DevOps与CI/CD", "ROS与机器人",
    "Yocto与嵌入式构建", "企业级项目", "元工具与工程流程", "博客与知识发布",
    "学习与示例", "嵌入式与驱动", "独立产品与应用", "笔记与知识库",
    "运维与监控", "Web与前端",
]

VISIBILITY_VALUES = ["public", "private"]  # TSK-009 #5：英文值域

# 列说明行文案（TSK-009 #4：第 2 行为对该列的解释）
COLUMN_DOCS = {
    "repos": {
        "name": "仓库名 owner/repo.git（唯一键；yoctoproject 允许裸 repo.git）",
        "path": "检出路径（唯一，不以 / 开头；自有行空则 sync 补 project/<repo>）",
        "branch": "分支（自有行由 excel-sync 按 API default_branch 刷新）",
        "platform": "托管平台 gitee/github/gitlab/yoctoproject（外键→remotes 表）",
        "protocol": "协议覆盖 https/git（留空=default_protocol；自有行由 sync 清空）",
        "topic": "主题（slug 用于 by-topic 维度）",
        "language": "主语言（slug 用于 by-language 维度）",
        "groups": "手填同步组，逗号分隔；生成时自动追加 platform/topic/visibility-public|private 派生组",
        "linkfiles": "软链 src:dest，多条分号分隔（人工维护，自动化永不覆盖）",
        "description": "仓库描述（自有行由 excel-sync 从 API 刷新）",
        "purpose": "仓库用途（人工知识列，自动化永不覆盖）",
        "contents": "主要内容（人工知识列）",
        "relations": "仓库间关系（人工知识列）",
        "仓库属性": "public/private（自有行由 excel-sync 按 API visibility 刷新）",
        "标签分类": "统一标签体系（下拉可选，清单维护于统计表）",
        "仓库大小(KB)": "仓库体积 KB（自有行由 excel-sync 刷新；gitlab/yoctoproject 无公开 API 留空）",
        "suggested_action": "维护建议（保留/更新/待确认/废弃，自由文本）",
        "note": "备注（上游消失标注等）",
    },
    "remotes": {
        "platform": "平台名（repos.platform 外键）",
        "https_url": "HTTPS fetch 地址",
        "git_url": "git:// fetch 地址（可空）",
        "proxy_https_url": "代理 HTTPS fetch 地址（use_proxy_https=TRUE 时生效）",
    },
    "config": {
        "键": "配置键",
        "值": "配置值",
        "说明": "含义",
    },
}

HEADER_FILL = PatternFill("solid", fgColor="37474F")   # 深蓝灰表头（低饱和暗色）
DOCS_FILL = PatternFill("solid", fgColor="E3E9F0")     # 列说明行底色
BAND_FILL_A = PatternFill("solid", fgColor="D6DEE7")   # 数据行条纹-深（偶数行）
BAND_FILL_B = PatternFill("solid", fgColor="EBEFF4")   # 数据行条纹-浅（奇数行）
TITLE_FILL = PatternFill("solid", fgColor="263238")    # 标题行

# 长文本列：固定上限宽 + 单元格内换行（name/path/groups/linkfiles 内容长且相邻列非空，
# 无法溢出显示，同样依赖换行完整呈现）
WRAP_COLUMNS = {"name", "path", "groups", "linkfiles",
                "description", "purpose", "contents", "relations", "suggested_action", "note"}


def _style_sheet(ws, header: list, band: bool = False) -> None:
    """三行结构样式：1 表头 / 2 列说明 / 3+ 数据（双色条纹）。"""
    ws.freeze_panes = f"A{DATA_START_ROW}"
    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = Font(bold=True, color="FFFFFF")
    sheet_docs = COLUMN_DOCS.get(ws.title, {})
    for cell in ws[DOCS_ROW]:
        cell.fill = DOCS_FILL
        cell.font = Font(italic=True, size=9, color="546E7A")
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        doc = sheet_docs.get(str(cell.value or ""), "")
        if doc:
            cell.value = doc
    if band:
        # 逐单元格双色条纹：xlsx 行级 fill 不生效（Excel/WPS 均忽略）。
        for row_idx in range(DATA_START_ROW, ws.max_row + 1):
            fill = BAND_FILL_A if row_idx % 2 == 0 else BAND_FILL_B
            for cell in ws[row_idx]:
                cell.fill = fill
                if str(header[cell.column - 1] if cell.column - 1 < len(header) else "") in WRAP_COLUMNS:
                    cell.alignment = Alignment(wrap_text=True, vertical="top")


def _tight_widths(ws) -> None:
    """紧凑列宽：内容自适应（CJK 按双宽计），封顶 28；不设固定行高（打开自动）。"""
    for column_cells in ws.columns:
        letter = get_column_letter(column_cells[0].column)
        header_name = str(ws.cell(1, column_cells[0].column).value or "")
        cjk_width = 0
        for c in column_cells:
            v = str(c.value) if c.value is not None else ""
            w = sum(2 if ord(ch) > 0x2E7F else 1 for ch in v)
            cjk_width = max(cjk_width, w)
        width = min(cjk_width + 2, MAX_COL_WIDTH)
        if header_name in WRAP_COLUMNS:
            width = min(max(width, 14), MAX_COL_WIDTH)
        ws.column_dimensions[letter].width = width


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
    ws["B3"].value = "=COUNTA(repos!$A:$A)-2"  # 减表头+说明行（TSK-009 三行结构）
    ws["A4"].value = "public"
    ws["B4"].value = f'=COUNTIF(repos!${attr_letter}:${attr_letter},"public")'
    ws["A5"].value = "private"
    ws["B5"].value = f'=COUNTIF(repos!${attr_letter}:${attr_letter},"private")'
    ws["A6"].value = "public 占比"
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


README_ROWS = [
    ("A.流程|1", "修改入口：CI 人工触发 excel-validate，基于 base 分支（默认 main）创建 excel/update-<时间戳> 分支并完成校验与规范化（含下拉与统计公式刷新），产生且仅一个提交，不自动合并。"),
    ("A.流程|2", "人工流转：拉取该分支→本地修改 Excel→推送→合并回主分支→删除该分支。"),
    ("A.流程|3", "合并后人工触发 excel-sync：同步自有仓库（上游消失的行将被删除、新增仓库自动追加）→刷新动态统计与图表→确定性重建 manifests→--check→有差异才提交（[skip ci]）。"),
    ("A.流程|4", "自有行（name 以 config.self_owner 开头）由自动化维护：branch/platform/description/仓库属性/仓库大小自动刷新；人工维护 path（已有值不覆盖）与 groups/topic/知识列（永不覆盖）。"),
    ("B.结构|1", "repos/remotes/config 三表均为三行结构：第 1 行表头（下拉自第 1 行即可点选）/第 2 行列说明/第 3 行起数据。"),
    ("B.结构|2", "标签分类列下拉=内联枚举（14 类）+TagCategories 命名区域双保险；统计表按 public/private 与标签自动计数（COUNTIF/COUNTA）。"),
    ("B.字典|repos.protocol", "https/git；留空继承 config.default_protocol。"),
    ("B.字典|repos.仓库属性", "public/private（GitHub API 实值，excel-sync 自动刷新）。"),
    ("B.字典|repos.仓库大小(KB)", "GitHub API size 字段（KB），excel-sync 自动刷新；gitee 等平台无对应 API 指标则留空。"),
    ("B.字典|repos.topic", "主题标签，驱动 by-topic 维度文件与 groups 派生属性（TSK-010）。"),
    ("B.字典|repos.language", "语言标签，驱动 by-language 维度；excel-sync 对 github 自有行按 GitHub API 实测回填。"),
    ("B.字典|动态统计", "GitHub API 实时拉取 stars/forks/size/pushed_at，含 4 张图表（标签分布条形/平台饼/size Top15 条形/public-private 饼）；gitee/gitlab/yoctoproject 平台指标留空。"),
    ("C.指引|1", "双轨分工：groups/topic=manifest 拉取维度（技术栈/生态），标签分类=管理统计维度（业务属性）；两者由不同场景使用，不强行合并。"),
    ("C.指引|2", "文档目录与命名规范见 AGENTS.md §6；完整使用说明见 docs/00-guide/GUIDE-20261128-001。"),
]


def _refresh_readme(wb) -> None:
    """重写 readme sheet 文案（TSK-011 R6）：与三行结构/英文值域/动态统计现状同步。"""
    ws = wb["readme"]
    if ws.max_row > 1:
        ws.delete_rows(2, ws.max_row - 1)
    for i, (k, v) in enumerate(README_ROWS, start=2):
        ws.cell(row=i, column=1).value = k
        ws.cell(row=i, column=2).value = v


def _apply_formatting(path: Path, platform_values: list) -> None:
    wb = load_workbook(path)
    enum_columns = {
        "protocol": ["https", "git"],
        "仓库属性": VISIBILITY_VALUES,
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
            _style_sheet(ws, [c.value for c in ws[1]], band=True)
            _tight_widths(ws)
        # refresh dropdowns: remove old ones on repos, re-add non-strict hints.
        # 范围从第 1 行开始（TSK-011）：表头单元格即可点选下拉（用户复查确认）。
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
            dv.add(f"{letter}1:{letter}1000")
            repos.add_data_validation(dv)
        # 标签分类下拉双保险（TSK-009 #3）：
        # ① 内联枚举串（任何 Excel/WPS 版本直接可点选；由统计表清单生成）；
        # ② TagCategories 命名区域（文档化引用，跨表单区域引用的规范写法）。
        if "TagCategories" in wb.defined_names:
            del wb.defined_names["TagCategories"]
        wb.defined_names["TagCategories"] = DefinedName(
            "TagCategories", attr_text=f"统计!$A${tag_start}:$A${tag_end}"
        )
        tag_letter = get_column_letter(header.index("标签分类") + 1)
        dv = DataValidation(
            type="list",
            formula1='"' + ",".join(TAG_CATEGORIES) + '"',
            allow_blank=True,
            showErrorMessage=False,
        )
        dv.add(f"{tag_letter}1:{tag_letter}1000")
        repos.add_data_validation(dv)
        _refresh_readme(wb)
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
