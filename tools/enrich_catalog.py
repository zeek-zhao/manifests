# -*- coding: utf-8 -*-
"""Enrich catalogs/zeek-zhao.json with category / visibility / description /
suggested_action for every repository entry.

- category: the confirmed 13-class scheme (kept as-is per owner decision)
- visibility/description: fetched live from the GitHub API
- suggested_action: pending-decision notes; "保留" when none
- key order rewritten: identity -> classification -> manifest mechanics
- written ensure_ascii=True so the file stays ASCII-only (pre-commit
  pretty-format-json defaults to escaped non-ASCII)
"""
import json
import os
import urllib.request

CATALOG = os.path.join(os.path.dirname(__file__), "..", "catalogs", "zeek-zhao.json")

CATEGORY = {
    # 博客与知识发布
    "ai-obsidian": "博客与知识发布",
    "hexo-engine": "博客与知识发布",
    "zeek-zhao.github.io": "博客与知识发布",
    "PagePipe": "博客与知识发布",
    # AI 应用与工具（ai-workflow/ai-knowledge 维持原分类）
    "meetnote": "AI应用与工具",
    "ai-workflow": "AI应用与工具",
    "ai-knowledge": "AI应用与工具",
    # 独立产品 / 应用
    "kuaidian": "独立产品与应用",
    "linkManager": "独立产品与应用",
    "WorthTrack": "独立产品与应用",
    # 企业级项目
    "FlexDev-Ent": "企业级项目",
    "fron-backframe": "企业级项目",
    "fron-backframe-refactor": "企业级项目",
    # DevOps 与 CI/CD
    "orgflow-devops": "DevOps与CI/CD",
    "orgflow-devops1": "DevOps与CI/CD",
    "orgflow-jenkins": "DevOps与CI/CD",
    "jenkins": "DevOps与CI/CD",
    "jenkins-shared-library": "DevOps与CI/CD",
    "devops": "DevOps与CI/CD",
    # 运维与监控
    "srvkit": "运维与监控",
    "PromWatch": "运维与监控",
    "nas-server": "运维与监控",
    # Yocto 与嵌入式构建
    "poky": "Yocto与嵌入式构建",
    "yp-distro": "Yocto与嵌入式构建",
    # 嵌入式与驱动
    "linux-driver": "嵌入式与驱动",
    "free-rtos-demo": "嵌入式与驱动",
    "src800-bootloader": "嵌入式与驱动",
    # C++ 工具与桌面
    "package-manager": "C++工具与桌面",
    "qt-learn-code": "C++工具与桌面",
    # ROS 与机器人
    "ros": "ROS与机器人",
    "frobot": "ROS与机器人",
    # 学习与示例（devbox 维持原分类）
    "devbox": "学习与示例",
    "obsidian-sample": "学习与示例",
    "database-sample": "学习与示例",
    "vue-sample": "学习与示例",
    "rust-sample": "学习与示例",
    "standard-version": "学习与示例",
    "base-sample": "学习与示例",
    "python-sample": "学习与示例",
    "go-sample": "学习与示例",
    "java-sample": "学习与示例",
    "cpp-sample": "学习与示例",
    "LanguageLearning": "学习与示例",
    "product-sample": "学习与示例",
    "docker-sample": "学习与示例",
    # 笔记与知识库
    "obsidian": "笔记与知识库",
    "attachments": "笔记与知识库",
    # 待整理（catalog 内非 GitHub 盘点范围）
    "alpu": "待整理",
    # 元工具与工程流程
    "manifests": "元工具与工程流程",
}

PENDING = {
    "orgflow-devops1": "待确认：与 orgflow-devops 描述相同，保留其一",
    "devops": "待确认：无 README，补充说明或并入 orgflow 体系",
    "ai-knowledge": "待确认：定位待明确",
    "attachments": "待确认：附件多为个人内容，考虑转私有",
    "alpu": "待确认：gitee 条目，未纳入本次 GitHub 盘点",
}

HDRS = {
    "Authorization": "Bearer " + os.environ["GH_TOKEN"],
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "zeek-repo-tidy",
}


def fetch_github_repos():
    repos, page = {}, 1
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/user/repos?per_page=100&page={page}&sort=full_name",
            headers=HDRS)
        with urllib.request.urlopen(req) as r:
            chunk = json.loads(r.read())
        if not chunk:
            return repos
        for it in chunk:
            repos[it["full_name"]] = it
        page += 1


def repo_key(entry_name):
    # "zeek-zhao/manifests.git" -> ("zeek-zhao", "manifests")
    return entry_name.removesuffix(".git").split("/", 1)


def main():
    with open(CATALOG, encoding="utf-8") as f:
        data = json.load(f)

    gh = fetch_github_repos()
    print(f"github api: {len(gh)} repos visible")

    missing_cat = []
    for entry in data["repositories"]:
        owner, name = repo_key(entry["name"])
        if entry.get("platform") != "github" or f"{owner}/{name}" not in gh:
            info = {}
        else:
            info = gh[f"{owner}/{name}"]

        cat = CATEGORY.get(name)
        if cat is None:
            missing_cat.append(name)
            cat = "待分类"

        action = PENDING.get(name, "保留")
        if info.get("archived"):
            action = "已归档"

        rebuilt = {
            "name": entry["name"],
            "path": entry["path"],
            "branch": entry["branch"],
            "category": cat,
            "visibility": "private" if info.get("private") else
                          ("public" if info else ""),
            "description": info.get("description") or "",
            "suggested_action": action,
        }
        # 保留其余既有字段（topic/language/platform/groups/preferred_protocol/...）
        for k, v in entry.items():
            if k not in rebuilt:
                rebuilt[k] = v
        entry.clear()
        entry.update(rebuilt)

    if missing_cat:
        raise SystemExit(f"unmapped categories: {missing_cat}")

    with open(CATALOG, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")

    cats = {}
    for e in data["repositories"]:
        cats[e["category"]] = cats.get(e["category"], 0) + 1
    print("entries:", len(data["repositories"]))
    for c in sorted(cats, key=cats.get, reverse=True):
        print(f"  {c}: {cats[c]}")
    pending = [e["name"] for e in data["repositories"]
               if e["suggested_action"].startswith("待确认")]
    print("pending:", len(pending), pending)


if __name__ == "__main__":
    main()
