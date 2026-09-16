from __future__ import annotations

from dataclasses import dataclass

import pytest

from ksupervisor import extensions
from models.extension import ExtensionSignatureStatus
from persistence.sqlite_store import SQLitePersistenceStore


@dataclass(frozen=True)
class FakeDistribution:
    name: str
    version: str
    requires: tuple[str, ...]


class FakePoint:
    def __init__(self, *, distribution, loaded, name="demo-agent", value="demo:agent"):
        self.group = extensions.EXTENSION_GROUPS["agent"]
        self.name = name
        self.value = value
        self.dist = distribution
        self.loaded = loaded
        self.load_count = 0

    def load(self):
        self.load_count += 1
        return self.loaded


class FakePoints(tuple):
    def select(self, *, group):
        return FakePoints(item for item in self if item.group == group)


def _distribution(version="1.0.0", requirement="k-supervisor>=0.1,<0.2"):
    return FakeDistribution("demo-extension", version, (requirement,))


def _govern(store, descriptor, *, enabled=True, trusted=True, signature_status=ExtensionSignatureStatus.VERIFIED):
    governance = extensions.ExtensionGovernance(store, platform_version="0.1.0")
    governance.set_policy(
        descriptor,
        enabled=enabled,
        trusted=trusted,
        signature_status=signature_status,
        provenance="wheel:demo-extension",
        verification_reference=("sigstore:verified-demo" if signature_status == ExtensionSignatureStatus.VERIFIED else None),
    )
    return governance


def test_trusted_extension_activates_and_governance_survives_restart(monkeypatch, tmp_path):
    point = FakePoint(distribution=_distribution(), loaded=lambda context: context.require("marker"))
    monkeypatch.setattr(extensions.metadata, "entry_points", lambda: FakePoints((point,)))
    descriptor = extensions.discover_extensions("agent")[0]
    assert point.load_count == 0
    assert descriptor.distribution == "demo-extension"
    assert descriptor.distribution_version == "1.0.0"
    assert descriptor.platform_constraint == ">=0.1,<0.2"
    assert descriptor.identity

    path = tmp_path / "state.db"
    with SQLitePersistenceStore(path) as store:
        governance = _govern(store, descriptor)
        context = extensions.ExtensionContext({"marker": "trusted"})
        assert extensions.activate_extension("agent", "demo-agent", context, governance) == "trusted"
        assert point.load_count == 1

    with SQLitePersistenceStore(path) as store:
        governance = extensions.ExtensionGovernance(store, platform_version="0.1.0")
        persisted = store.get_extension_trust(descriptor.identity)
        assert persisted is not None and persisted.enabled and persisted.trusted
        context = extensions.ExtensionContext({"marker": "after-restart"})
        assert extensions.activate_extension("agent", "demo-agent", context, governance) == "after-restart"
        assert point.load_count == 2


def test_installed_extension_requires_governance_before_import(monkeypatch):
    point = FakePoint(distribution=_distribution(), loaded=lambda context: None)
    monkeypatch.setattr(extensions.metadata, "entry_points", lambda: FakePoints((point,)))
    with pytest.raises(extensions.ExtensionActivationError, match="requires governance"):
        extensions.activate_extension("agent", "demo-agent", extensions.ExtensionContext({}))
    assert point.load_count == 0


@pytest.mark.parametrize(
    ("enabled", "trusted", "signature_status", "message"),
    [
        (False, True, ExtensionSignatureStatus.VERIFIED, "disabled"),
        (True, False, ExtensionSignatureStatus.VERIFIED, "not trusted"),
        (True, True, ExtensionSignatureStatus.UNVERIFIED, "not verified"),
    ],
)
def test_policy_rejections_happen_before_import(
    monkeypatch, tmp_path, enabled, trusted, signature_status, message
):
    point = FakePoint(distribution=_distribution(), loaded=lambda context: None)
    monkeypatch.setattr(extensions.metadata, "entry_points", lambda: FakePoints((point,)))
    descriptor = extensions.discover_extensions("agent")[0]
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        governance = _govern(
            store,
            descriptor,
            enabled=enabled,
            trusted=trusted,
            signature_status=signature_status,
        )
        with pytest.raises(extensions.ExtensionActivationError, match=message):
            extensions.activate_extension("agent", "demo-agent", extensions.ExtensionContext({}), governance)
    assert point.load_count == 0


@pytest.mark.parametrize(
    ("requirement", "message"),
    [
        ("other-package>=1", "compatibility declaration is missing"),
        ("k-supervisor>=0.2,<0.3", "incompatible"),
        ("k-supervisor>=broken", "compatibility declaration is invalid"),
    ],
)
def test_incompatible_or_missing_declaration_fails_before_import(monkeypatch, tmp_path, requirement, message):
    point = FakePoint(distribution=_distribution(requirement=requirement), loaded=lambda context: None)
    monkeypatch.setattr(extensions.metadata, "entry_points", lambda: FakePoints((point,)))
    descriptor = extensions.discover_extensions("agent")[0]
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        governance = extensions.ExtensionGovernance(store, platform_version="0.1.0")
        if descriptor.platform_constraint is not None:
            governance.set_policy(
                descriptor,
                enabled=True,
                trusted=True,
                signature_status=ExtensionSignatureStatus.VERIFIED,
                provenance="wheel:demo-extension",
                verification_reference="sigstore:verified-demo",
            )
        with pytest.raises(extensions.ExtensionActivationError, match=message):
            extensions.activate_extension("agent", "demo-agent", extensions.ExtensionContext({}), governance)
    assert point.load_count == 0


def test_trust_does_not_follow_changed_distribution_identity(monkeypatch, tmp_path):
    original = FakePoint(distribution=_distribution("1.0.0"), loaded=lambda context: None)
    monkeypatch.setattr(extensions.metadata, "entry_points", lambda: FakePoints((original,)))
    descriptor = extensions.discover_extensions("agent")[0]
    with SQLitePersistenceStore(tmp_path / "state.db") as store:
        governance = _govern(store, descriptor)
        changed = FakePoint(distribution=_distribution("1.1.0"), loaded=lambda context: None)
        monkeypatch.setattr(extensions.metadata, "entry_points", lambda: FakePoints((changed,)))
        with pytest.raises(extensions.ExtensionActivationError, match="no trust decision"):
            extensions.activate_extension("agent", "demo-agent", extensions.ExtensionContext({}), governance)
        assert changed.load_count == 0
