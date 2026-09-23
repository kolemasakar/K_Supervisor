from pathlib import Path
import re


WORKFLOWS = Path(".github/workflows")
USES = re.compile(r"uses:\s+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)")


def test_all_external_actions_are_pinned_to_full_commit_sha():
    offenders = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = USES.search(line)
            if match and not re.fullmatch(r"[0-9a-f]{40}", match.group(2)):
                offenders.append(f"{path}:{line.strip()}")
    assert offenders == []


def test_expected_action_pins_are_documented_with_human_readable_refs():
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(WORKFLOWS.glob("*.yml"))
    )
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in text
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7" in text
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7" in text
    assert "actions/download-artifact@37930b1c2abaa49bbe596cd826c3c89aef350131 # v7" in text
    assert "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33 # release/v1" in text
