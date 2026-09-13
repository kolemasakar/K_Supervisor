from pathlib import Path


def test_phase14_has_no_legacy_runtime_import():
    source = Path("workflows/reference_loop.py").read_text(encoding="utf-8")
    assert "K_Research_Critic" not in source
    assert "research_critic_loop" not in source
    assert "ProfileWorkflow" not in source
