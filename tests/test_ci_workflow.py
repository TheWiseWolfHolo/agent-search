from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_validates_pull_requests_and_main_on_supported_runtime_edges():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    required_markers = [
        "pull_request:",
        "branches:",
        "- main",
        "permissions:",
        "contents: read",
        "ubuntu-latest",
        "windows-latest",
        'python: "3.10"',
        'python: "3.13"',
        'node: "20"',
        'node: "24"',
        "actions/checkout@v6",
        "actions/setup-python@v6",
        "actions/setup-node@v6",
        "run: npm ci",
        "run: npm test",
    ]

    for marker in required_markers:
        assert marker in workflow
