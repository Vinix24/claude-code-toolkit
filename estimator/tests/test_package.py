"""The skill folder holds together: names match across files and nothing reaches for a model SDK."""
from __future__ import annotations

import os
import re

import compute_estimate as ce
from conftest import PKG


def test_guide_topics_exist_in_the_example_table():
    topics = set(ce.parse_benchmarks(PKG / "benchmarks.example.md")) | {"analysis_only"}
    guide = (PKG / "references" / "topic-mix-guide.md").read_text()
    named = set(re.findall(r"`([a-z_]+)` \d", guide))
    assert named, "the guide should name topics with block counts"
    assert named <= topics, f"topics in the guide but not in the example table: {sorted(named - topics)}"


def test_guide_dependency_types_have_a_default_premium():
    from estimator_config import DEFAULTS
    guide = (PKG / "references" / "topic-mix-guide.md").read_text()
    section = guide.split("## External dependencies", 1)[1].split("\n## ", 1)[0]
    listed = set(re.findall(r"^\| `([a-z_0-9]+)` \|", section, re.M))
    assert listed == set(DEFAULTS["external_dep_premiums"])


def test_skill_frontmatter():
    text = (PKG / "SKILL.md").read_text()
    front = text.split("---", 2)[1]
    assert re.search(r"^name: estimator$", front, re.M)
    assert re.search(r"^description: .{80,}", front, re.M)


def test_scripts_use_the_standard_library_only():
    for path in (PKG / "scripts").glob("*.py"):
        source = path.read_text()
        assert not re.search(r"^\s*(import|from)\s+(anthropic|openai|requests|httpx)\b", source, re.M), path.name


def test_installer_is_executable():
    assert os.access(PKG / "install.sh", os.X_OK)
