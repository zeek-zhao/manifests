import sys
import unittest
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from generate_manifests import build_render_plan, merge_catalogs


CATALOG_CPP = {
    "remotes": {
        "github": {
            "https": "https://github.com",
            "git": "ssh://git@github.com"
        }
    },
    "repositories": [
        {
            "name": "bazelbuild/examples.git",
            "path": "code/cpp/bazel_examples",
            "branch": "main",
            "topic": "c++",
            "platform": "github",
            "language": "c/c++",
            "groups": ["c++"]
        }
    ]
}


CATALOG_ZEEK = {
    "remotes": {
        "gitee": {
            "https": "https://gitee.com",
            "git": "ssh://git@gitee.com"
        }
    },
    "owners": {
        "zeek-zhao": {
            "preferred_protocol": "git",
            "groups": ["owner-zeek-zhao"]
        }
    },
    "repositories": [
        {
            "name": "zeek-zhao/docker-sample.git",
            "path": "sample/docker-sample",
            "branch": "master",
            "topic": "common",
            "platform": "github",
            "language": "nodejs",
            "groups": ["common"],
            "linkfiles": [
                {
                    "src": ".",
                    "dest": "sample/cpp-sample/docker"
                }
            ]
        }
    ]
}


class MergeCatalogsTest(unittest.TestCase):
    def test_multiple_catalogs_are_merged(self) -> None:
        merged = merge_catalogs([CATALOG_CPP, CATALOG_ZEEK])

        self.assertIn("github", merged["remotes"])
        self.assertIn("gitee", merged["remotes"])
        self.assertIn("zeek-zhao", merged["owners"])
        self.assertEqual(2, len(merged["repositories"]))


class BuildRenderPlanTest(unittest.TestCase):
    def test_quickstart_example_manifests_are_generated(self) -> None:
        merged = merge_catalogs([CATALOG_CPP, CATALOG_ZEEK])
        plan = build_render_plan(merged)

        https_example = plan["manifests/examples/quickstart-https.xml"]
        ssh_example = plan["manifests/examples/quickstart-zeek-zhao.xml"]

        self.assertIn('name="bazelbuild/examples.git"', https_example)
        self.assertIn('remote="github_https"', https_example)
        self.assertIn('name="zeek-zhao/docker-sample.git"', ssh_example)
        self.assertIn('remote="github_git"', ssh_example)

    def test_linkfiles_are_rendered_when_present(self) -> None:
        merged = merge_catalogs([CATALOG_CPP, CATALOG_ZEEK])
        plan = build_render_plan(merged)

        owner_manifest = plan["manifests/generated/by-owner/zeek-zhao.xml"]

        self.assertIn('include name="manifests/_remotes.xml"', owner_manifest)
        self.assertIn('<linkfile src="." dest="sample/cpp-sample/docker" />', owner_manifest)
        self.assertIn('remote="github_git"', owner_manifest)

    def test_default_manifest_contains_generated_indexes(self) -> None:
        merged = merge_catalogs([CATALOG_CPP, CATALOG_ZEEK])
        plan = build_render_plan(merged)

        default_manifest = plan["manifests/default.xml"]

        self.assertIn('include name="manifests/generated/by-owner/zeek-zhao.xml"', default_manifest)
        self.assertIn('include name="manifests/generated/by-topic/cpp.xml"', default_manifest)

    def test_project_groups_only_contain_groups_platform_topic(self) -> None:
        merged = merge_catalogs([CATALOG_CPP, CATALOG_ZEEK])
        plan = build_render_plan(merged)

        owner_manifest = plan["manifests/generated/by-owner/zeek-zhao.xml"]

        self.assertIn('groups="common,github"', owner_manifest)
        self.assertNotIn('owner-zeek-zhao', owner_manifest)
        self.assertNotIn(',git,', owner_manifest)
        self.assertNotIn(',https,', owner_manifest)
        self.assertNotIn(',nodejs', owner_manifest)


if __name__ == "__main__":
    unittest.main()
