import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    from openpyxl import load_workbook as _load_xlsx
except ImportError:  # pragma: no cover - excel mode is optional
    _load_xlsx = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOGS_DIR = PROJECT_ROOT / "catalogs"
MANIFEST_ROOT = PROJECT_ROOT / "manifests"
DEFAULT_XLSX = CATALOGS_DIR / "manifests.xlsx"
DEFAULT_SNAPSHOT = CATALOGS_DIR / "manifests-excel-snapshot.json"
SNAPSHOT_NAME = DEFAULT_SNAPSHOT.name
DEFAULT_PROTOCOL = "https"
INCLUDE_HEADERS = ["manifests/_remotes.xml", "manifests/_hooks.xml"]
QUICKSTART_EXAMPLES = {
    "manifests/examples/quickstart-https.xml": {
        "repo_name": "bazelbuild/examples.git",
        "protocol": "https",
    },
    "manifests/examples/quickstart-zeek-zhao.xml": {
        "repo_name": "zeek-zhao/docker-sample.git",
        "protocol": "git",
    },
}
REPO_COLUMNS = [
    "name", "path", "branch", "platform", "protocol", "topic", "language",
    "groups", "linkfiles", "description", "purpose", "contents", "relations",
    "visibility", "category", "suggested_action", "note",
]
REMOTE_COLUMNS = ["platform", "https_url", "git_url", "proxy_https_url"]
VALID_PROTOCOLS = {"", "https", "git"}
NAME_RE = re.compile(r"^[^/\s]+(/[^/\s]+)?\.git$")


def slugify(value: str) -> str:
    slug = value.strip().lower()
    replacements = {
        "c/c++": "c-cpp",
        "c++": "cpp",
        " ": "-",
        "/": "-",
        "+": "p",
        ".": "-",
    }
    for old, new in replacements.items():
        slug = slug.replace(old, new)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def unique(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def get_owner(repo_name: str) -> str:
    owner, _, _ = repo_name.partition("/")
    return owner


def merge_catalogs(catalogs: List[Dict]) -> Dict:
    merged = {
        "remotes": {},
        "owners": {},
        "repositories": [],
    }
    for catalog in catalogs:
        merged["remotes"].update(catalog.get("remotes", {}))
        merged["owners"].update(catalog.get("owners", {}))
        merged["repositories"].extend(catalog.get("repositories", []))
    return merged


def _s(value) -> str:
    return "" if value is None else str(value).strip()


def _split_groups(value: str) -> List[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _split_linkfiles(value: str, row_no: int, errors: List[str]) -> List[Dict[str, str]]:
    if not value:
        return []
    items = []
    for part in value.split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            errors.append(f"repos row {row_no}: linkfiles 语法错误（应为 src:dest，分号分隔）：{part}")
            continue
        src, dest = part.split(":", 1)
        items.append({"src": src.strip(), "dest": dest.strip()})
    return items


def load_from_excel(xlsx_path: Path) -> Dict:
    """Load the 4-sheet workbook into the generator's merged-catalog shape.

    Data source per DSN-20261128-001 (D1/D2); validation rules per DSN §9.
    Raises ValueError listing every violation with its Excel row number.
    """
    if _load_xlsx is None:
        raise RuntimeError("openpyxl is required for --excel mode (pip install openpyxl)")
    errors: List[str] = []
    wb = _load_xlsx(xlsx_path, read_only=True, data_only=True)
    try:
        for sheet in ("repos", "remotes", "config", "readme"):
            if sheet not in wb.sheetnames:
                raise ValueError(f"缺少 sheet: {sheet}（实际: {wb.sheetnames}）")

        config: Dict[str, str] = {}
        ws = wb["config"]
        for row in ws.iter_rows(min_row=2, values_only=True):
            key = _s(row[0]) if row else ""
            if key:
                config[key] = _s(row[1]) if len(row) > 1 else ""

        remotes: Dict[str, Dict[str, str]] = {}
        ws = wb["remotes"]
        for row in ws.iter_rows(min_row=2, values_only=True):
            platform = _s(row[0]) if row else ""
            if not platform:
                continue
            remotes[platform] = {
                "https": _s(row[1]) if len(row) > 1 else "",
                "git": _s(row[2]) if len(row) > 2 else "",
                "proxy_https": _s(row[3]) if len(row) > 3 else "",
            }
            if not remotes[platform]["https"] and not remotes[platform]["git"]:
                errors.append(f"remotes 行 {platform}: https_url/git_url 均为空")
        if not remotes:
            errors.append("remotes 表为空")

        ws = wb["repos"]
        header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
        missing = [c for c in REPO_COLUMNS if c not in header]
        if missing:
            raise ValueError(f"repos 表缺少列: {missing}")
        idx = {name: header.index(name) for name in REPO_COLUMNS}
        repositories: List[Dict] = []
        seen_paths: Dict[str, int] = {}
        slug_seen: Dict[str, Dict[str, str]] = {"topic": {}, "language": {}}
        row_no = 1
        for row in ws.iter_rows(min_row=2, values_only=True):
            row_no += 1
            cells = {
                name: (_s(row[i]) if i < len(row) and row[i] is not None else "")
                for name, i in idx.items()
            }
            if not any(cells.values()):
                continue
            name, path = cells["name"], cells["path"]
            if not NAME_RE.match(name):
                errors.append(f"repos row {row_no}: name 格式应为 owner/repo.git（或裸 repo.git）：{name}")
            if not path:
                errors.append(f"repos row {row_no}: path 为空")
            elif ".." in path.split("/"):
                errors.append(f"repos row {row_no}: path 不允许包含 ..：{path}")
            elif path.startswith("/"):
                errors.append(f"repos row {row_no}: path 不允许以 / 开头：{path}")
            if path in seen_paths:
                errors.append(f"repos row {row_no}: path 重复（与 row {seen_paths[path]}）：{path}")
            else:
                seen_paths[path] = row_no
            if cells["platform"] not in remotes:
                errors.append(f"repos row {row_no}: platform 不在 remotes 表：{cells['platform']}")
            if cells["protocol"] not in VALID_PROTOCOLS:
                errors.append(f"repos row {row_no}: protocol 应为 https/git/留空：{cells['protocol']}")
            for field in ("topic", "language"):
                raw = cells[field]
                slug = slugify(raw) if raw else ""
                if raw and slug:
                    bucket = slug_seen[field]
                    if slug in bucket and bucket[slug] != raw:
                        errors.append(
                            f"repos row {row_no}: {field} slug 冲突：{raw} 与 {bucket[slug]} 同为 {slug}"
                        )
                    bucket[slug] = raw
            repositories.append({
                "name": name,
                "path": path,
                "branch": cells["branch"],
                "platform": cells["platform"],
                "preferred_protocol": cells["protocol"] or None,
                "topic": cells["topic"],
                "language": cells["language"],
                "groups": _split_groups(cells["groups"]),
                "linkfiles": _split_linkfiles(cells["linkfiles"], row_no, errors),
                "description": cells["description"],
                "purpose": cells["purpose"],
                "contents": cells["contents"],
                "relations": cells["relations"],
                "visibility": cells["visibility"],
                "category": cells["category"],
                "suggested_action": cells["suggested_action"],
                "note": cells["note"],
                "_row": row_no,
            })
        if errors:
            raise ValueError("Excel 校验失败（DSN §9）:\n" + "\n".join(errors))
        owners: Dict[str, Dict] = {}
        self_owner = config.get("self_owner", "")
        if self_owner and any(r["name"].startswith(self_owner + "/") for r in repositories):
            owners[self_owner] = {}
        return {
            "remotes": remotes,
            "owners": owners,
            "repositories": repositories,
            "config": config,
            "_use_proxy_https": config.get("use_proxy_https", "").upper() == "TRUE",
        }
    finally:
        wb.close()


def get_effective_protocol(config: Dict, repo: Dict, requested_protocol: str = None) -> str:
    owner_name = get_owner(repo["name"])
    owner_config = config.get("owners", {}).get(owner_name, {})
    repo_protocol = repo.get("preferred_protocol")
    owner_protocol = owner_config.get("preferred_protocol")
    if requested_protocol:
        if repo_protocol == "git" or owner_protocol == "git":
            return "git"
        return requested_protocol
    return repo_protocol or owner_protocol or DEFAULT_PROTOCOL


def build_groups(config: Dict, repo: Dict, protocol: str) -> List[str]:
    repo_groups = repo.get("groups", [])
    return unique(repo_groups + [repo["platform"], repo["topic"]])


def build_project_entry(config: Dict, repo: Dict, requested_protocol: str = None) -> Dict:
    protocol = get_effective_protocol(config, repo, requested_protocol)
    branch = repo["branch"]
    return {
        "name": repo["name"],
        "path": repo["path"],
        "remote": f'{repo["platform"]}_{protocol}',
        "groups": build_groups(config, repo, protocol),
        "dest_branch": branch,
        "revision": f"refs/heads/{branch}",
        "linkfiles": repo.get("linkfiles", []),
    }


def find_repository(config: Dict, repo_name: str) -> Dict:
    for repo in config.get("repositories", []):
        if repo["name"] == repo_name:
            return repo
    raise KeyError(repo_name)


def render_project(project: Dict) -> List[str]:
    lines = [
        "    <project "
        f'path="{project["path"]}" '
        f'remote="{project["remote"]}" '
        f'groups="{",".join(project["groups"])}" '
        f'name="{project["name"]}" '
        f'dest-branch="{project["dest_branch"]}" '
        f'revision="{project["revision"]}"'
        + (" >" if project["linkfiles"] else " />")
    ]
    for linkfile in project["linkfiles"]:
        lines.append(
            f'        <linkfile src="{linkfile["src"]}" dest="{linkfile["dest"]}" />'
        )
    if project["linkfiles"]:
        lines.append("    </project>")
    return lines


def render_xml_manifest(projects: List[Dict]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<manifest>']
    for include_name in INCLUDE_HEADERS:
        lines.append(f'    <include name="{include_name}" />')
    if projects:
        lines.append("")
    for project in projects:
        lines.extend(render_project(project))
    lines.append("</manifest>")
    return "\n".join(lines) + "\n"


def render_index_manifest(include_paths: Iterable[str]) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<manifest>']
    for include_path in include_paths:
        lines.append(f'    <include name="{include_path}" />')
    lines.append("</manifest>")
    return "\n".join(lines) + "\n"


def render_hooks() -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<manifest>',
            '    <include name="manifests/_remotes.xml" />',
            '</manifest>',
            '',
        ]
    )


def render_remotes(config: Dict) -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<manifest>']
    protocol_comments = {
        "git": "使用 Git over SSH 协议",
        "https": "使用 HTTPS 协议",
    }
    remotes = config.get("remotes", {})
    use_proxy_https = bool(config.get("_use_proxy_https"))
    for protocol in ["git", "https"]:
        lines.append(f'    <!-- {protocol_comments[protocol]} -->')
        for platform in sorted(remotes):
            entry = remotes[platform]
            fetch = entry[protocol]
            attrs = [f'name="{platform}_{protocol}"', f'fetch="{fetch}"']
            if protocol == "git":
                attrs.append(f'pushurl="{fetch}"')
            elif use_proxy_https and entry.get("proxy_https") and entry["proxy_https"] != fetch:
                # DSN §7.1 / K4: proxy only rewrites the https fetch URL;
                # pushurl always stays on the real address.
                attrs[1] = f'fetch="{entry["proxy_https"]}"'
                attrs.append(f'pushurl="{fetch}"')
            lines.append(f'    <remote {" ".join(attrs)} />')
        lines.append("")
    if lines[-1] == "":
        lines.pop()
    lines.append("</manifest>")
    return "\n".join(lines) + "\n"


def _quickstart_examples(config: Dict) -> Dict[str, Dict[str, str]]:
    cfg = config.get("config") or {}
    https_repo = cfg.get("quickstart_https_repo")
    self_repo = cfg.get("quickstart_self_repo")
    if https_repo and self_repo:
        return {
            "manifests/examples/quickstart-https.xml": {
                "repo_name": https_repo,
                "protocol": "https",
            },
            "manifests/examples/quickstart-zeek-zhao.xml": {
                "repo_name": self_repo,
                "protocol": "git",
            },
        }
    return QUICKSTART_EXAMPLES


def build_render_plan(config: Dict) -> Dict[str, str]:
    plan: Dict[str, str] = {}
    by_protocol: Dict[str, List[Dict]] = defaultdict(list)
    by_platform: Dict[str, List[Dict]] = defaultdict(list)
    by_language: Dict[str, List[Dict]] = defaultdict(list)
    by_topic: Dict[str, List[Dict]] = defaultdict(list)
    by_owner: Dict[str, List[Dict]] = defaultdict(list)

    for repo in config.get("repositories", []):
        project = build_project_entry(config, repo)
        protocol = get_effective_protocol(config, repo)
        owner = get_owner(repo["name"])
        by_protocol[protocol].append(project)
        if repo["platform"]:
            by_platform[repo["platform"]].append(project)
        language_slug = slugify(repo["language"])
        if language_slug:
            by_language[language_slug].append(project)
        topic_slug = slugify(repo["topic"])
        if topic_slug:
            by_topic[topic_slug].append(project)
        if owner in config.get("owners", {}):
            by_owner[owner].append(project)

    plan["manifests/_remotes.xml"] = render_remotes(config)
    plan["manifests/_hooks.xml"] = render_hooks()

    include_index: List[str] = []
    for protocol, projects in sorted(by_protocol.items()):
        path = f"manifests/generated/by-protocol/{protocol}.xml"
        plan[path] = render_xml_manifest(projects)
        include_index.append(f"generated/by-protocol/{protocol}.xml")

    for platform, projects in sorted(by_platform.items()):
        path = f"manifests/generated/by-platform/{platform}.xml"
        plan[path] = render_xml_manifest(projects)
        include_index.append(f"generated/by-platform/{platform}.xml")

    for language, projects in sorted(by_language.items()):
        path = f"manifests/generated/by-language/{language}.xml"
        plan[path] = render_xml_manifest(projects)
        include_index.append(f"generated/by-language/{language}.xml")

    for topic, projects in sorted(by_topic.items()):
        path = f"manifests/generated/by-topic/{topic}.xml"
        plan[path] = render_xml_manifest(projects)
        include_index.append(f"generated/by-topic/{topic}.xml")

    for owner, projects in sorted(by_owner.items()):
        path = f"manifests/generated/by-owner/{owner}.xml"
        plan[path] = render_xml_manifest(projects)
        include_index.append(f"generated/by-owner/{owner}.xml")

    for path, example in _quickstart_examples(config).items():
        repo = find_repository(config, example["repo_name"])
        project = build_project_entry(config, repo, example["protocol"])
        plan[path] = render_xml_manifest([project])

    plan["manifests/default.xml"] = render_index_manifest(
        sorted(f"manifests/{path}" for path in include_index)
    )
    return plan


def load_catalogs(catalogs_dir: Path) -> List[Dict]:
    catalogs = []
    for catalog_file in sorted(catalogs_dir.glob("*.json")):
        if catalog_file.name == SNAPSHOT_NAME:
            continue
        catalogs.append(json.loads(catalog_file.read_text(encoding="utf-8")))
    return catalogs


SNAPSHOT_REPO_ORDER = [
    "name", "path", "branch", "platform", "protocol", "topic", "language",
    "groups", "linkfiles", "description", "purpose", "contents", "relations",
    "visibility", "category", "suggested_action", "note",
]


def export_snapshot(merged: Dict, out_path: Path) -> None:
    repositories = []
    for repo in merged.get("repositories", []):
        item = {key: repo.get(key) for key in SNAPSHOT_REPO_ORDER}
        item["protocol"] = repo.get("preferred_protocol") or ""
        repositories.append(item)
    payload = {
        "repositories": repositories,
        "remotes": {
            platform: {
                key: entry[key]
                for key in ("https", "git", "proxy_https")
                if key in entry
            }
            for platform, entry in merged.get("remotes", {}).items()
        },
        "config": merged.get("config", {}),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # keep default ensure_ascii=True: committed JSON catalogs are \uXXXX-escaped
    # by the pretty-format-json pre-commit hook, and the snapshot must match.
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_plan(root: Path, plan: Dict[str, str]) -> None:
    for relative_path, content in plan.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def check_plan(root: Path, plan: Dict[str, str]) -> Tuple[bool, List[str]]:
    mismatches = []
    for relative_path, expected in plan.items():
        target = root / relative_path
        actual = target.read_text(encoding="utf-8") if target.exists() else None
        if actual != expected:
            mismatches.append(relative_path)
    return not mismatches, mismatches


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate repo manifests from the Excel workbook (DSN D1/D2) or legacy JSON catalogs."
    )
    parser.add_argument("--catalogs-dir", type=Path, default=CATALOGS_DIR)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--excel", action="store_true",
        help="read catalogs/manifests.xlsx instead of JSON catalogs",
    )
    parser.add_argument(
        "--xlsx", type=Path, default=DEFAULT_XLSX,
        help="Excel workbook path for --excel mode (default: catalogs/manifests.xlsx)",
    )
    parser.add_argument(
        "--export-json", nargs="?", const=str(DEFAULT_SNAPSHOT), default=None,
        help="export the Excel data as a JSON snapshot (requires --excel)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.excel:
            merged = load_from_excel(args.xlsx)
            if args.export_json:
                export_snapshot(merged, Path(args.export_json))
        else:
            if args.export_json:
                print("--export-json requires --excel")
                return 2
            merged = merge_catalogs(load_catalogs(args.catalogs_dir))
        plan = build_render_plan(merged)
    except (ValueError, RuntimeError) as exc:
        print(exc)
        return 1
    if args.check:
        valid, mismatches = check_plan(args.output, plan)
        if not valid:
            for mismatch in mismatches:
                print(mismatch)
            return 1
        return 0
    write_plan(args.output, plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
