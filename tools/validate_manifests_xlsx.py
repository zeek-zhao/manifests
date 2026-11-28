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
import re
import sys
import zipfile
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
MAX_COL_WIDTH = 28          # 兼容保留（TSK-015 分级后未直接使用）
MAX_WRAP_WIDTH = 26         # 长文本列（wrap）上限（TSK-015 D-4）
MAX_PLAIN_WIDTH = 18        # 普通列上限（TSK-015 D-4）
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
        "仓库大小(MB)": "仓库体积 MB（自有行由 excel-sync 刷新；gitlab/yoctoproject 无公开 API 留空）",
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


NARROW_COLUMNS = {"branch", "platform", "仓库属性", "标签分类", "仓库大小(MB)",
                  "suggested_action", "value", "key", "区块"}


def _tight_widths(ws) -> None:
    """紧凑列宽三级（TSK-015 #2）：长文本列 26 封顶（wrap）；普通列 18 封顶；
    窄值列按内容+2、不设下限，整表尽量一页可视。不设固定行高（打开自动）。"""
    for column_cells in ws.columns:
        letter = get_column_letter(column_cells[0].column)
        header_name = str(ws.cell(1, column_cells[0].column).value or "")
        cjk_width = 0
        for c in column_cells:
            if c.row == 2:
                continue  # TSK-015：说明行文本不参与列宽（靠 wrap 显示），窄列不被撑宽
            v = str(c.value) if c.value is not None else ""
            w = sum(2 if ord(ch) > 0x2E7F else 1 for ch in v)
            cjk_width = max(cjk_width, w)
        if header_name in WRAP_COLUMNS:
            width = min(max(cjk_width + 2, 14), MAX_WRAP_WIDTH)
        elif header_name in NARROW_COLUMNS:
            width = min(max(cjk_width + 2, 8), MAX_PLAIN_WIDTH)
        else:
            width = min(cjk_width + 2, MAX_PLAIN_WIDTH)
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
    ("A.流程|4", "自有行（name 以 config.self_owner 开头）由自动化维护：branch/platform/description/仓库属性/仓库大小(MB)自动刷新；人工维护 path（已有值不覆盖）与 groups/topic/知识列（永不覆盖）。"),
    ("B.结构|1", "repos/remotes/config 三表均为三行结构：第 1 行表头（下拉自第 1 行即可点选）/第 2 行列说明/第 3 行起数据。"),
    ("B.结构|2", "标签分类列下拉=内联枚举（14 类）+TagCategories 命名区域双保险；统计表按 public/private 与标签自动计数（COUNTIF/COUNTA）。"),
    ("B.字典|repos.仓库属性", "public/private（GitHub API 实值，excel-sync 自动刷新）。"),
    ("B.字典|repos.仓库大小(MB)", "GitHub API size/1024（MB，保留 1 位小数），excel-sync 自动刷新；gitee 等平台无对应 API 指标则留空。"),
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


def _collect_values(ws) -> dict:
    """逐列收集数据全集（第 3 行起，排除第 2 行说明行），去重排序去空（TSK-013）。"""
    header = [c.value for c in ws[1]]
    out = {}
    for idx, col_name in enumerate(header, start=1):
        vals = sorted({
            str(ws.cell(row=r, column=idx).value).strip()
            for r in range(3, ws.max_row + 1)
            if ws.cell(row=r, column=idx).value not in (None, "")
        })
        if vals:
            out[col_name] = vals
    return out


def _dropdown_source(wb, col_name: str, values: list, dd_state: dict) -> str:
    """超长值域写入「下拉源」sheet 新列并注册 DD<n> 命名区域，返回区域名。"""
    if "下拉源" not in wb.sheetnames:
        wb.create_sheet("下拉源")
    ws = wb["下拉源"]
    dd_state["idx"] += 1
    idx = dd_state["idx"]
    letter = get_column_letter(idx)
    ws.cell(row=1, column=idx).value = col_name
    for i, v in enumerate(values, start=2):
        ws.cell(row=i, column=idx).value = v
    name = f"DD{idx}"
    wb.defined_names[name] = DefinedName(
        name, attr_text=f"下拉源!${letter}$2:${letter}${1 + len(values)}"
    )
    return name


def _apply_column_dv(ws, col_name: str, values: list, wb, dd_state: dict) -> None:
    """单列 DV：值域内联 ≤255 字符，否则引用下拉源命名区域；sqref=第 3 行起（TSK-014：
    第 1 行表头交互归 AutoFilter 筛选，DV 不再覆盖表头；第 2 行说明行始终排除）。"""
    header = [c.value for c in ws[1]]
    letter = get_column_letter(header.index(col_name) + 1)
    inline = '"' + ",".join(values) + '"'
    if len(inline) <= 255:
        formula1 = inline
    else:
        formula1 = _dropdown_source(wb, col_name, values, dd_state)
    dv = DataValidation(
        type="list", formula1=formula1, allow_blank=True, showErrorMessage=False
    )
    dv.add(f"{letter}3:{letter}1000")
    ws.add_data_validation(dv)


def _rebuild_total_row(ws) -> None:
    """TSK-015 #3：repos 表末尾「合计」行（仓库大小(MB) 列 SUM 数据区，加粗）。
    先删旧合计行再重建，保证幂等；数据行数以最后一个非空 name 行为准。"""
    for r in range(DATA_START_ROW, ws.max_row + 1):
        if str(ws.cell(row=r, column=1).value or "").strip() == "合计":
            ws.delete_rows(r)
            break
    last = DATA_START_ROW - 1
    for r in range(DATA_START_ROW, ws.max_row + 1):
        if str(ws.cell(row=r, column=1).value or "").strip():
            last = r
    size_col = None
    for c in range(1, ws.max_column + 1):
        if str(ws.cell(row=1, column=c).value or "").strip() == "仓库大小(MB)":
            size_col = c
            break
    total_row = last + 1
    ws.cell(row=total_row, column=1).value = "合计"
    if size_col:
        letter = get_column_letter(size_col)
        ws.cell(row=total_row, column=size_col).value = f"=SUM({letter}{DATA_START_ROW}:{letter}{last})"
    for c in range(1, ws.max_column + 1):
        ws.cell(row=total_row, column=c).font = Font(bold=True)


def _apply_formatting(path: Path, platform_values: list) -> None:
    wb = load_workbook(path)
    # 重建下拉源：清除旧 sheet 与 DD* 命名区域（TSK-013）
    if "下拉源" in wb.sheetnames:
        wb.remove(wb["下拉源"])
    for n in [n for n in wb.defined_names if n.startswith("DD")]:
        del wb.defined_names[n]
    dd_state = {"idx": 0}
    try:
        repos = wb["repos"]
        header = [c.value for c in repos[1]]
        tag_start, tag_end = _rebuild_stats(wb, header, platform_values)
        _rebuild_total_row(repos)  # TSK-015：合计行幂等重建（在样式前，行数纳入条纹区间可接受）
        for name in ("repos", "remotes", "config", "readme"):
            ws = wb[name]
            _style_sheet(ws, [c.value for c in ws[1]], band=True)
            _tight_widths(ws)
        _refresh_readme(wb)
        # 清空四表旧 DV 后按「每列一枚举」矩阵重建（TSK-014：DV 仅数据区；表头=AutoFilter）。
        for sheet_name in ("repos", "remotes", "config", "readme"):
            ws = wb[sheet_name]
            for dv in list(ws.data_validations.dataValidation):
                ws.data_validations.dataValidation.remove(dv)
        values_by_sheet = {
            n: _collect_values(wb[n]) for n in ("remotes", "config", "readme")
        }
        repo_vals = _collect_values(repos)
        # 表头筛选（TSK-014）：四表 AutoFilter，ref 自表头行 1 起覆盖实际数据区；
        # 点击表头箭头=筛选菜单（自动列出列内去重值、勾选后隐藏不匹配行）。
        for sheet_name in ("repos", "remotes", "config", "readme"):
            ws = wb[sheet_name]
            ws.auto_filter.ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
        # 枚举固定列：固定值域优先于数据全集（维持既有语义）。
        repo_vals["仓库属性"] = VISIBILITY_VALUES
        repo_vals["标签分类"] = list(TAG_CATEGORIES)
        if platform_values:
            repo_vals["platform"] = platform_values
        repo_vals["suggested_action"] = ["保留", "更新", "待确认", "废弃"]
        for col_name in header:  # 值域治理：空列补占位；自由文本/超长值域列配占位枚举
            vals = repo_vals.get(col_name)
            if not vals:
                repo_vals[col_name] = ["（暂无可选项）"]
            elif max(len(str(v)) for v in vals) > 40 or len(
                '"' + ",".join(str(v) for v in vals) + '"'
            ) > 255:
                repo_vals[col_name] = ["（自由填写）"]
        for col_name, vals in repo_vals.items():
            if col_name in header and vals:
                _apply_column_dv(repos, col_name, vals, wb, dd_state)
        for sheet_name in ("remotes", "config", "readme"):
            ws = wb[sheet_name]
            for col_name, vals in values_by_sheet[sheet_name].items():
                _apply_column_dv(ws, col_name, vals, wb, dd_state)
        # openpyxl 层自检：repos DV 数 == 表头列数；sqref 不含第 1/2 行（TSK-014）。
        expect = len(header)
        got = len(repos.data_validations.dataValidation)
        if got != expect:
            raise ValueError(f"repos 表 DV 数 {got} != 表头列数 {expect}")
        for dv in repos.data_validations.dataValidation:
            for seg in str(dv.sqref).split():
                if re.fullmatch(r"[A-Z]+[12]", seg) or re.search(r"[A-Z]+[12]:", seg):
                    raise ValueError(f"repos 表 sqref 覆盖了第 1/2 行: {seg}")
        for sheet_name in ("repos", "remotes", "config", "readme"):
            ref = wb[sheet_name].auto_filter.ref
            if not ref or not ref.startswith("A1:"):
                raise ValueError(f"{sheet_name}: AutoFilter ref 缺失或未自第 1 行起: {ref!r}")
        # 标签分类下拉双保险（TSK-009 #3）：内联枚举串 + TagCategories 命名区域。
        if "TagCategories" in wb.defined_names:
            del wb.defined_names["TagCategories"]
        wb.defined_names["TagCategories"] = DefinedName(
            "TagCategories", attr_text=f"统计!$A${tag_start}:$A${tag_end}"
        )
        # normalize 是工作簿最后写手：openpyxl 重存会丢 autoFilter（CI pip 未钉版本行为漂移，
        # 前序 sync/stats 写点同样可能丢）——保存前统一回填，保证 verify 与终态成立。
        for name in ("repos", "remotes", "config", "readme"):
            ws = wb[name]
            if not ws.auto_filter.ref:
                ws.auto_filter.ref = ws.dimensions
        wb.save(path)
        # openpyxl 3.1.x 强制为每个 DV 写出 showDropDown="0"：
        # Excel 对该属性语义反转（0=显示箭头），而 WPS 等按字面义处理（0=不显示）。
        # 唯一双兼容写法是省略属性 → 保存后用 zip 后处理剥除，并自检。
        _sanitize_dropdowns(path)
        _verify_dropdowns(path)
    finally:
        wb.close()


def _sanitize_dropdowns(path: Path) -> None:
    """zip rewrite: strip showDropDown attributes and stale x14 dataValidation
    extLst blocks (openpyxl round-trips keep them, producing ghost dropdowns)."""
    tmp = path.with_suffix(".tmp.xlsx")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(
        tmp, "w", zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if re.match(r"xl/worksheets/sheet\d+\.xml$", item.filename):
                xml = data.decode("utf-8")
                xml = re.sub(r'\s+showDropDown="[01]"', "", xml)
                # TSK-014: drop extLst blocks that only carry stale x14 data
                # validations (openpyxl never clears extLst on DV removal).
                xml = re.sub(
                    r"<extLst>(?:(?!</extLst>).)*x14:dataValidations(?:(?!</extLst>).)*</extLst>",
                    "",
                    xml,
                    flags=re.DOTALL,
                )
                data = xml.encode("utf-8")
            zout.writestr(item, data)
    tmp.replace(path)


def _verify_dropdowns(path: Path) -> None:
    """Post-save assertions: no showDropDown attr; DV sqref never rows 1-2
    (header interaction is AutoFilter since TSK-014); formula1 is a quoted inline
    list (<=255 chars) or a DD<n> name; sheets 1-4 carry an A1-anchored autoFilter."""
    with zipfile.ZipFile(path) as z:
        autofilter_sheets = []
        for name in z.namelist():
            ms_sheet = re.match(r"xl/worksheets/sheet(\d+)\.xml$", name)
            if not ms_sheet:
                continue
            xml = z.read(name).decode("utf-8")
            if 'showDropDown="' in xml:
                raise ValueError(f"{name}: showDropDown attribute still present")
            af = re.search(r'<autoFilter\b[^>]*\bref="([^"]+)"', xml)
            if af:
                autofilter_sheets.append(int(ms_sheet.group(1)))
                if not af.group(1).startswith("A1:"):
                    raise ValueError(f"{name}: autoFilter ref not A1-anchored: {af.group(1)}")
            if 'showDropDown="' in xml:
                raise ValueError(f"{name}: showDropDown attribute still present")
            if "x14:dataValidation" in xml:
                raise ValueError(f"{name}: stale x14 dataValidation extLst remains")
            # sqref must be read from standard <dataValidation> tags only —
            # x14 extLst copies are stripped by _sanitize and must not resurrect.
            for m_dv in re.finditer(r"<dataValidation\b[^>]*>", xml):
                msq = re.search(r'sqref="([^"]+)"', m_dv.group(0))
                if not msq:
                    continue
                for part in msq.group(1).split():
                    if (
                        re.fullmatch(r"[A-Z]+[12]", part)
                        or re.search(r"[A-Z]+[12]:", part)
                    ):
                        raise ValueError(f"{name}: sqref 覆盖了第 1/2 行: {part}")
        missing = [n for n in (1, 2, 3, 4) if n not in autofilter_sheets]
        if missing:
            raise ValueError(
                f"expected autoFilter on sheets 1-4 (repos/remotes/config/readme), missing {missing}; got {autofilter_sheets}"
            )
        # repos sheet (sheet1.xml): every list DV must start at row 3 with a quoted
        # inline list (<=255 chars) or a DD<n> defined-name reference (TSK-013/014).
        workbook_xml = z.read("xl/workbook.xml").decode("utf-8")
        defined = set(re.findall(r'<definedName name="(DD\d+)"', workbook_xml))
        xml = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        dvs = 0
        for tag in re.finditer(r"<dataValidation\b[^>]*>", xml):
            t = tag.group(0)
            ms = re.search(r'sqref="([^"]+)"', t)
            if 'type="list"' not in t:
                if ms:
                    raise ValueError(f"repos sheet: non-list DV at {ms.group(0)}")
                continue
            # TSK-014：sqref 必须为单段 X3:X1000（数据区；表头交互归 AutoFilter）。
            if not ms or not re.fullmatch(
                r"[A-Z]+3:[A-Z]+\d+", ms.group(1).strip()
            ):
                raise ValueError(
                    f"repos sheet: list DV must cover data rows from row 3, got {t[:140]}"
                )
            dvs += 1
        import html as _html

        for f1 in [_html.unescape(m.group(1)) for m in re.finditer(r"<formula1>([^<]*)</formula1>", xml)] + [
            _html.unescape(m.group(1)) for m in re.finditer(r'formula1="([^"]*)"', xml)
        ]:
            if f1.startswith('"') and f1.endswith('"'):
                if len(f1) > 255:
                    raise ValueError(f"repos sheet: inline list >255 chars ({len(f1)})")
            elif not re.fullmatch(r"DD\d+", f1) or f1 not in defined:
                raise ValueError(f"repos sheet: bad formula1 {f1!r}")
        if dvs == 0:
            raise ValueError("repos sheet: no list data validations found")


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
