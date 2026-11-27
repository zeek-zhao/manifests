#!/usr/bin/env python3
"""Validate / normalize / snapshot the Excel workbook (DSN-20261128-001 §9, §11).

Modes:
  default        validate structure and rules only (CI safe, no writes)
  --normalize    rewrite formatting: freeze header row, bold header, column
                 widths, and refresh enum dropdowns (non-strict hints)
  --export-json  additionally export a JSON snapshot of the workbook
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_manifests as gm  # noqa: E402
from openpyxl import load_workbook  # noqa: E402
from openpyxl.styles import Font  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = PROJECT_ROOT / "catalogs" / "manifests.xlsx"
DEFAULT_SNAPSHOT = PROJECT_ROOT / "catalogs" / "manifests-excel-snapshot.json"
MAX_COL_WIDTH = 60


def _apply_formatting(path: Path, platform_values: list) -> None:
    wb = load_workbook(path)
    enum_columns = {
        "protocol": list(gm.VALID_PROTOCOLS.__class__(("https", "git"))),
        "visibility": ["public", "private", "internal"],
        "suggested_action": ["保留", "更新", "待确认", "废弃"],
    }
    if platform_values:
        enum_columns["platform"] = platform_values
    try:
        repos = wb["repos"]
        for sheet_name in ("repos", "remotes", "config", "readme"):
            ws = wb[sheet_name]
            ws.freeze_panes = "A2"
            for cell in ws[1]:
                cell.font = Font(bold=True)
        for ws in (repos, wb["remotes"], wb["config"], wb["readme"]):
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
        header = [c.value for c in repos[1]]
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
