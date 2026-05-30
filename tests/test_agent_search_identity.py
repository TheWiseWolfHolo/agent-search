import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_package_metadata_uses_wolfholo_agent_search_identity():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    lockfile = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert package["name"] == "@thewisewolfholo/agent-search"
    assert package["bin"] == {"agent-search": "npm/bin/agent-search.js"}
    assert package["homepage"] == "https://github.com/TheWiseWolfHolo/agent-search#readme"
    assert package["repository"]["url"] == "git+https://github.com/TheWiseWolfHolo/agent-search.git"
    assert package["bugs"]["url"] == "https://github.com/TheWiseWolfHolo/agent-search/issues"
    assert lockfile["name"] == "@thewisewolfholo/agent-search"
    assert lockfile["packages"][""]["name"] == "@thewisewolfholo/agent-search"
    assert lockfile["packages"][""]["bin"] == {"agent-search": "npm/bin/agent-search.js"}
    assert 'name = "agent-search"' in pyproject
    assert 'agent-search = "agent_search.cli:main"' in pyproject


def test_source_tree_uses_agent_search_python_package():
    assert (ROOT / "src" / "agent_search" / "cli.py").is_file()
    assert not (ROOT / "src" / "smart_search").exists()
    assert (ROOT / "npm" / "bin" / "agent-search.js").is_file()
    assert not (ROOT / "npm" / "bin" / "smart-search.js").exists()


def test_bundled_skill_uses_agent_search_cli_name():
    assert (ROOT / "skills" / "agent-search-cli" / "SKILL.md").is_file()
    assert (ROOT / "src" / "agent_search" / "assets" / "skills" / "agent-search-cli" / "SKILL.md").is_file()
    assert not (ROOT / "skills" / "smart-search-cli").exists()


def test_product_tree_has_no_removed_provider_surface():
    forbidden = [
        "ZHI" + "PU",
        "zhi" + "pu",
        "\u667a\u8c31",
        "big" + "model",
        "G" + "LM",
    ]
    roots = [
        ROOT / "src",
        ROOT / "tests",
        ROOT / "npm",
        ROOT / "skills",
        ROOT / ".github",
    ]
    files = [
        ROOT / "README.md",
        ROOT / "README.zh-CN.md",
        ROOT / "pyproject.toml",
        ROOT / "package.json",
        ROOT / "package-lock.json",
    ]
    for root in roots:
        files.extend(path for path in root.rglob("*") if path.is_file())

    offenders = []
    for path in files:
        if any(part in {".git", "__pycache__", ".pytest_cache"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in forbidden:
            if marker in text:
                offenders.append(str(path.relative_to(ROOT)))
                break

    assert offenders == []
