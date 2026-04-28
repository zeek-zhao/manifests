import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOGS_DIR = PROJECT_ROOT / "catalogs"
MANIFEST_ROOT = PROJECT_ROOT / "manifests"
DEFAULT_PROTOCOL = "https"
INCLUDE_HEADERS = ["manifests/_remotes.xml", "manifests/_hooks.xml"]


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
    owner_name = get_owner(repo["name"])
    owner_groups = config.get("owners", {}).get(owner_name, {}).get("groups", [])
    repo_groups = repo.get("groups", [])
    language_group = slugify(repo["language"])
    return unique(owner_groups + repo_groups + [repo["platform"], protocol, language_group])


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
    for protocol in ["git", "https"]:
        lines.append(f'    <!-- {protocol_comments[protocol]} -->')
        for platform in sorted(remotes):
            fetch = remotes[platform][protocol]
            attrs = [f'name="{platform}_{protocol}"', f'fetch="{fetch}"']
            if protocol == "git":
                attrs.append(f'pushurl="{fetch}"')
            lines.append(f'    <remote {" ".join(attrs)} />')
        lines.append("")
    if lines[-1] == "":
        lines.pop()
    lines.append("</manifest>")
    return "\n".join(lines) + "\n"


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
        by_platform[repo["platform"]].append(project)
        by_language[slugify(repo["language"])] .append(project)
        by_topic[slugify(repo["topic"])] .append(project)
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

    plan["manifests/default.xml"] = render_index_manifest(
        sorted(f"manifests/{path}" for path in include_index)
    )
    return plan


def load_catalogs(catalogs_dir: Path) -> List[Dict]:
    catalogs = []
    for catalog_file in sorted(catalogs_dir.glob("*.json")):
        catalogs.append(json.loads(catalog_file.read_text(encoding="utf-8")))
    return catalogs


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
    parser = argparse.ArgumentParser(description="Generate repo manifests from multiple catalog files.")
    parser.add_argument("--catalogs-dir", type=Path, default=CATALOGS_DIR)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    merged = merge_catalogs(load_catalogs(args.catalogs_dir))
    plan = build_render_plan(merged)
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
