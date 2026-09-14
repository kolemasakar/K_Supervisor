from __future__ import annotations

from dataclasses import dataclass

from ksupervisor import extensions


@dataclass(frozen=True)
class FakePoint:
    group: str
    name: str
    value: str
    loaded: object
    dist: object | None = None

    def load(self):
        return self.loaded


class FakePoints(tuple):
    def select(self, *, group):
        return FakePoints(item for item in self if item.group == group)


def test_all_supported_extension_kinds_are_discoverable(monkeypatch):
    points = FakePoints(
        FakePoint(group, f"demo-{kind}", f"demo:{kind}", lambda context: context.require("marker"))
        for kind, group in extensions.EXTENSION_GROUPS.items()
    )
    monkeypatch.setattr(extensions.metadata, "entry_points", lambda: points)

    found = extensions.discover_extensions()
    assert {item.kind for item in found} == set(extensions.EXTENSION_GROUPS)

    context = extensions.ExtensionContext({"marker": "registered-without-supervisor-change"})
    for kind in extensions.EXTENSION_GROUPS:
        assert extensions.activate_extension(kind, f"demo-{kind}", context) == "registered-without-supervisor-change"


def test_unknown_extension_kind_is_rejected():
    try:
        extensions.discover_extensions("unknown")
    except ValueError as exc:
        assert "unknown extension kind" in str(exc)
    else:
        raise AssertionError("unknown extension kind must fail")
