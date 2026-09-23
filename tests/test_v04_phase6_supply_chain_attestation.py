from pathlib import Path
import re


WORKFLOW = Path(".github/workflows/supply-chain-attestation.yml")


def test_supply_chain_attestation_is_trusted_main_only_and_least_privilege():
    text = WORKFLOW.read_text(encoding="utf-8")
    trigger_block = text.split("jobs:", 1)[0]
    assert "push:" in trigger_block
    assert "branches: [main]" in trigger_block
    assert "workflow_dispatch:" in trigger_block
    assert "pull_request:" not in trigger_block
    assert "contents: read" in trigger_block
    assert "id-token: write" in trigger_block
    assert "attestations: write" in trigger_block
    assert "github.ref == 'refs/heads/main'" in text
    assert "secrets." not in text


def test_supply_chain_attestation_uses_pinned_official_actions_and_exact_artifacts():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in text
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7" in text
    assert "actions/attest-build-provenance@977bb373ede98d70efdf65b84cb5f73e068dcc2a # v3" in text
    assert "actions/attest-sbom@4651f806c01d8637787e274ac3bdf724ef169f34 # v3" in text
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7" in text
    assert "--lock-file requirements/ci-py313.lock" in text
    assert '--commit "${GITHUB_SHA}"' in text
    assert "dist/k-supervisor.spdx.json" in text
    assert "dist/supply-chain-evidence.json" in text


def test_supply_chain_attestation_has_no_mutable_external_action_refs():
    text = WORKFLOW.read_text(encoding="utf-8")
    refs = re.findall(r"uses:\s+[^@\s]+@([^\s#]+)", text)
    assert refs
    assert all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in refs)
