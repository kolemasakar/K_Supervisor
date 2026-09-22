import io
import json

import pytest

from observability import (
    ProductionMetricRegistry,
    ProductionObservability,
    StructuredLogger,
    TelemetryRecorder,
)
from release_manager import ReleaseManager
from release_manager.errors import ReleaseNotReadyError
from tests.phase13_support import NOW, build_release_stack


def _observer(store):
    sink = io.StringIO()
    metrics = ProductionMetricRegistry()
    return (
        ProductionObservability(
            telemetry=TelemetryRecorder(store),
            logger=StructuredLogger(sink),
            metrics=metrics,
        ),
        sink,
        metrics,
    )


def test_release_preparation_and_owner_handoff_emit_bounded_telemetry(tmp_path):
    store, registry, human, repos, repository = build_release_stack(tmp_path)
    observer, sink, metrics = _observer(store)
    try:
        manager = ReleaseManager(
            store,
            registry,
            repos,
            human,
            observability=observer,
        )
        outcome = manager.handle_first_working(
            "P13",
            "1.0.0",
            repository,
            NOW,
            satisfied_criteria=("release tests pass",),
        )
        assert outcome.release.status.value == "PUBLICATION_REQUIRED"
        records = store.list_telemetry_records("P13")
        events = [item.event_name for item in records]
        assert "release.prepare.started" in events
        assert "release.prepare.completed" in events
        assert "release.publication_required" in events

        serialized = json.dumps(
            [item.model_dump(mode="json") for item in records],
            sort_keys=True,
        )
        assert "GPT_STORE" in serialized
        assert "GPT_INSTRUCTIONS.md" not in serialized
        assert "release tests pass" not in serialized

        rendered = metrics.render_prometheus()
        assert 'target="GPT_STORE"' in rendered
        assert 'operation="prepare"' in rendered
        assert 'result="success"' in rendered
        assert 'operation="publication_handoff"' in rendered
        assert 'result="required"' in rendered

        log = sink.getvalue()
        assert "GPT_INSTRUCTIONS.md" not in log
        assert "release tests pass" not in log
    finally:
        store.close()


def test_release_not_ready_emits_failure_without_changing_exception_contract(tmp_path):
    store, registry, human, repos, repository = build_release_stack(tmp_path)
    observer, _, metrics = _observer(store)
    try:
        manager = ReleaseManager(
            store,
            registry,
            repos,
            human,
            observability=observer,
        )
        with pytest.raises(ReleaseNotReadyError):
            manager.handle_first_working(
                "P13",
                "1.0.0",
                repository,
                NOW,
                satisfied_criteria=(),
            )

        failed = [
            item
            for item in store.list_telemetry_records("P13")
            if item.event_name == "release.prepare.failed"
        ]
        assert failed
        assert failed[-1].attributes == {
            "target": "GPT_STORE",
            "operation": "prepare",
            "result": "failed",
            "error_code": "RELEASE_NOT_READY",
        }
        rendered = metrics.render_prometheus()
        assert 'target="GPT_STORE"' in rendered
        assert 'result="failed"' in rendered
    finally:
        store.close()


def test_release_observability_failure_is_non_authoritative(tmp_path):
    store, registry, human, repos, repository = build_release_stack(tmp_path)

    class BrokenObserver:
        def emit(self, **kwargs):
            raise RuntimeError("telemetry unavailable")

    try:
        manager = ReleaseManager(
            store,
            registry,
            repos,
            human,
            observability=BrokenObserver(),
        )
        outcome = manager.handle_first_working(
            "P13",
            "1.0.0",
            repository,
            NOW,
            satisfied_criteria=("release tests pass",),
        )
        assert outcome.release.status.value == "PUBLICATION_REQUIRED"
    finally:
        store.close()
