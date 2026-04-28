import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = PROJECT_ROOT.parent / "manifests" / "catalog" / "repositories.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "catalogs"


def get_owner(repo_name: str) -> str:
    owner, _, _ = repo_name.partition("/")
    return owner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split legacy repositories.json into multiple catalog files.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)

    cpp_catalog = {
        "repositories": [],
    }
    zeek_catalog = {
        "owners": source.get("owners", {}),
        "repositories": [],
    }
    community_github_catalog = {
        "remotes": source.get("remotes", {}),
        "repositories": [],
    }
    community_gitee_catalog = {
        "repositories": [],
    }
    community_gitlab_catalog = {
        "repositories": [],
    }
    community_yocto_catalog = {
        "repositories": [],
    }

    for repo in source.get("repositories", []):
        owner = get_owner(repo["name"])
        if owner == "zeek-zhao":
            zeek_catalog["repositories"].append(repo)
        elif repo.get("topic") == "c++":
            cpp_catalog["repositories"].append(repo)
        else:
            platform = repo.get("platform")
            if platform == "github":
                community_github_catalog["repositories"].append(repo)
            elif platform == "gitee":
                community_gitee_catalog["repositories"].append(repo)
            elif platform == "gitlab":
                community_gitlab_catalog["repositories"].append(repo)
            elif platform == "yoctoproject":
                community_yocto_catalog["repositories"].append(repo)
            else:
                community_github_catalog["repositories"].append(repo)

    targets = {
        "cpp.json": cpp_catalog,
        "zeek-zhao.json": zeek_catalog,
        "community-github.json": community_github_catalog,
        "community-gitee.json": community_gitee_catalog,
        "community-gitlab.json": community_gitlab_catalog,
        "community-yoctoproject.json": community_yocto_catalog,
    }
    for filename, content in targets.items():
        (args.output / filename).write_text(
            json.dumps(content, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
