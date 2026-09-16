from __future__ import annotations

import io
import json
from datetime import datetime, timezone

from models.enums import ProjectLifecycleState, ProjectOperationalState
from models.project import Project
from persistence import SQLitePersistenceStore
from registry import ProjectRegistry
from service_api import (
    LIFECYCLE_WRITE_SCOPE,
    OPERATIONAL_WRITE_SCOPE,
    READ_SCOPE,
    ServiceApiV1,
    ServicePrincipal,
    StaticBearerAuthenticator,
    WsgiServiceAppV1,
)

NOW = datetime(2026, 9, 16, 13, 0, tzinfo=timezone.utc)


def make_project(
    project_id: str = "P5API",
    *,
    lifecycle: ProjectLifecycleState = ProjectLifecycleState.IDEA,
    operational: ProjectOperationalState = ProjectOperationalState.ACTIVE,
) -> Project:
    return Project(
        project_id=project_id,
        name=project_id,
        lifecycle_state=lifecycle,
        operational_state=operational,
        created_at=NOW,
        updated_at=NOW,
    )


def principal(*scopes: str) -> ServicePrincipal:
    return ServicePrincipal(principal_id="owner-service", scopes=frozenset(scopes))


def open_api(path):
    store = SQLitePersistenceStore(path)
    store.initialize()
    projects = ProjectRegistry(store)
    return store, projects, ServiceApiV1(projects, store)


def test_v1_read_contract_returns_only_project_surface(tmp_path):
    store, projects, api = open_api(tmp_path / "state.db")
    projects.register(make_project("P1"))
    projects.register(make_project("P2", lifecycle=ProjectLifecycleState.BUILDING))
    response = api.dispatch("GET", "/api/v1/projects", principal=principal(READ_SCOPE))
    assert response.status_code == 200
    assert response.body["api_version"] == "v1"
    assert [item["project_id"] for item in response.body["data"]["projects"]] == ["P1", "P2"]
    assert "repository" not in response.body["data"]["projects"][0]
    assert "integrations" not in response.body["data"]["projects"][0]
    single = api.dispatch("GET", "/api/v1/projects/P2", principal=principal(READ_SCOPE))
    assert single.status_code == 200
    assert single.body["data"]["project"]["lifecycle_state"] == "BUILDING"
    store.close()


def test_v1_access_control_fails_closed_and_scopes_are_independent(tmp_path):
    store, projects, api = open_api(tmp_path / "state.db")
    projects.register(make_project())
    unauthenticated = api.dispatch("GET", "/api/v1/projects", principal=None)
    assert unauthenticated.status_code == 401
    assert unauthenticated.body["error"]["code"] == "AUTH_REQUIRED"
    under_scoped = api.dispatch("GET", "/api/v1/projects", principal=principal(LIFECYCLE_WRITE_SCOPE))
    assert under_scoped.status_code == 403
    assert under_scoped.body["error"]["code"] == "ACCESS_DENIED"
    denied_write = api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(READ_SCOPE), idempotency_key="access-test", body={"to_state": "ONBOARDING", "reason": "begin", "trigger": "owner"})
    assert denied_write.status_code == 403
    assert projects.get("P5API").lifecycle_state == ProjectLifecycleState.IDEA
    store.close()


def test_lifecycle_mutation_uses_authoritative_registry_and_audit(tmp_path):
    store, projects, api = open_api(tmp_path / "state.db")
    projects.register(make_project())
    response = api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(LIFECYCLE_WRITE_SCOPE), idempotency_key="life-1", body={"to_state": "ONBOARDING", "reason": "start onboarding", "trigger": "OWNER_API"})
    assert response.status_code == 200
    assert response.body["meta"]["idempotent_replay"] is False
    assert projects.get("P5API").lifecycle_state == ProjectLifecycleState.ONBOARDING
    transitions = store.list_lifecycle_transitions("P5API")
    assert len(transitions) == 1
    assert transitions[0].reason == "start onboarding"
    audit = store.list_audit_events("P5API")
    assert [item.event_type for item in audit] == ["PROJECT_LIFECYCLE_TRANSITION"]
    assert len(store.list_service_mutations("P5API")) == 1
    store.close()


def test_operational_mutation_has_separate_write_scope(tmp_path):
    store, projects, api = open_api(tmp_path / "state.db")
    projects.register(make_project())
    response = api.dispatch("POST", "/api/v1/projects/P5API/operational-transitions", principal=principal(OPERATIONAL_WRITE_SCOPE), idempotency_key="ops-1", body={"to_state": "PAUSED"})
    assert response.status_code == 200
    assert projects.get("P5API").operational_state == ProjectOperationalState.PAUSED
    assert len(store.list_operational_transitions("P5API")) == 1
    store.close()


def test_invalid_transition_is_409_and_does_not_mutate_history(tmp_path):
    store, projects, api = open_api(tmp_path / "state.db")
    projects.register(make_project())
    response = api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(LIFECYCLE_WRITE_SCOPE), idempotency_key="invalid-1", body={"to_state": "RELEASE_READY", "reason": "skip", "trigger": "OWNER_API"})
    assert response.status_code == 409
    assert response.body["error"]["code"] == "INVALID_TRANSITION"
    assert projects.get("P5API").lifecycle_state == ProjectLifecycleState.IDEA
    assert store.list_lifecycle_transitions("P5API") == ()
    assert store.list_audit_events("P5API") == ()
    assert store.list_service_mutations("P5API") == ()
    store.close()


def test_idempotent_mutation_replays_without_duplicate_transition_or_audit(tmp_path):
    store, projects, api = open_api(tmp_path / "state.db")
    projects.register(make_project())
    body = {"to_state": "ONBOARDING", "reason": "begin", "trigger": "OWNER_API"}
    first = api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(LIFECYCLE_WRITE_SCOPE), idempotency_key="replay-1", body=body)
    replay = api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(LIFECYCLE_WRITE_SCOPE), idempotency_key="replay-1", body=body)
    assert first.status_code == replay.status_code == 200
    assert first.body["meta"]["idempotent_replay"] is False
    assert replay.body["meta"]["idempotent_replay"] is True
    assert replay.body["data"]["project"] == first.body["data"]["project"]
    assert len(store.list_lifecycle_transitions("P5API")) == 1
    assert len(store.list_audit_events("P5API")) == 1
    assert len(store.list_service_mutations("P5API")) == 1
    store.close()


def test_same_idempotency_key_with_different_body_conflicts(tmp_path):
    store, projects, api = open_api(tmp_path / "state.db")
    projects.register(make_project())
    first = api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(LIFECYCLE_WRITE_SCOPE), idempotency_key="conflict-1", body={"to_state": "ONBOARDING", "reason": "begin", "trigger": "OWNER_API"})
    conflict = api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(LIFECYCLE_WRITE_SCOPE), idempotency_key="conflict-1", body={"to_state": "ONBOARDING", "reason": "changed", "trigger": "OWNER_API"})
    assert first.status_code == 200
    assert conflict.status_code == 409
    assert conflict.body["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert len(store.list_lifecycle_transitions("P5API")) == 1
    assert len(store.list_service_mutations("P5API")) == 1
    store.close()


def test_mutation_replay_survives_store_restart(tmp_path):
    path = tmp_path / "state.db"
    store, projects, api = open_api(path)
    projects.register(make_project())
    body = {"to_state": "ONBOARDING", "reason": "restart", "trigger": "OWNER_API"}
    first = api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(LIFECYCLE_WRITE_SCOPE), idempotency_key="restart-1", body=body)
    assert first.status_code == 200
    store.close()
    recovered_store, recovered_projects, recovered_api = open_api(path)
    replay = recovered_api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(LIFECYCLE_WRITE_SCOPE), idempotency_key="restart-1", body=body)
    assert replay.status_code == 200
    assert replay.body["meta"]["idempotent_replay"] is True
    assert recovered_projects.get("P5API").lifecycle_state == ProjectLifecycleState.ONBOARDING
    assert len(recovered_store.list_lifecycle_transitions("P5API")) == 1
    assert len(recovered_store.list_audit_events("P5API")) == 1
    snapshot = recovered_projects.recover("P5API")
    assert len(snapshot.service_mutations) == 1
    recovered_store.close()


def call_wsgi(app, method, path, *, token=None, body=None, idempotency_key=None):
    raw = b"" if body is None else json.dumps(body).encode("utf-8")
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw)}
    if token is not None:
        environ["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    if idempotency_key is not None:
        environ["HTTP_IDEMPOTENCY_KEY"] = idempotency_key
    captured = {}
    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)
    payload = b"".join(app(environ, start_response))
    return captured, json.loads(payload.decode("utf-8"))


def test_wsgi_http_adapter_applies_bearer_auth_json_and_idempotency(tmp_path):
    store, projects, api = open_api(tmp_path / "state.db")
    projects.register(make_project())
    auth = StaticBearerAuthenticator({"read-token": principal(READ_SCOPE), "write-token": principal(LIFECYCLE_WRITE_SCOPE)})
    app = WsgiServiceAppV1(api, auth)
    denied, denied_body = call_wsgi(app, "GET", "/api/v1/projects", token="wrong")
    assert denied["status"].startswith("401 ")
    assert denied_body["error"]["code"] == "AUTH_REQUIRED"
    ok, ok_body = call_wsgi(app, "GET", "/api/v1/projects", token="read-token")
    assert ok["status"].startswith("200 ")
    assert ok["headers"]["Content-Type"] == "application/json"
    assert ok["headers"]["Cache-Control"] == "no-store"
    assert ok_body["data"]["projects"][0]["project_id"] == "P5API"
    missing_key, missing_key_body = call_wsgi(app, "POST", "/api/v1/projects/P5API/lifecycle-transitions", token="write-token", body={"to_state": "ONBOARDING", "reason": "http", "trigger": "OWNER_API"})
    assert missing_key["status"].startswith("400 ")
    assert missing_key_body["error"]["code"] == "IDEMPOTENCY_REQUIRED"
    changed, changed_body = call_wsgi(app, "POST", "/api/v1/projects/P5API/lifecycle-transitions", token="write-token", idempotency_key="http-1", body={"to_state": "ONBOARDING", "reason": "http", "trigger": "OWNER_API"})
    assert changed["status"].startswith("200 ")
    assert changed_body["data"]["project"]["lifecycle_state"] == "ONBOARDING"
    store.close()


def test_wsgi_malformed_json_is_normalized_400(tmp_path):
    store, projects, api = open_api(tmp_path / "state.db")
    projects.register(make_project())
    app = WsgiServiceAppV1(api, StaticBearerAuthenticator({"write-token": principal(LIFECYCLE_WRITE_SCOPE)}))
    raw = b"{bad-json"
    environ = {"REQUEST_METHOD": "POST", "PATH_INFO": "/api/v1/projects/P5API/lifecycle-transitions", "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw), "HTTP_AUTHORIZATION": "Bearer write-token", "HTTP_IDEMPOTENCY_KEY": "bad-json-1"}
    captured = {}
    def start_response(status, headers):
        captured["status"] = status
    payload = b"".join(app(environ, start_response))
    body = json.loads(payload.decode("utf-8"))
    assert captured["status"].startswith("400 ")
    assert body["error"]["code"] == "INVALID_REQUEST"
    assert projects.get("P5API").lifecycle_state == ProjectLifecycleState.IDEA
    store.close()


def test_invalid_request_enum_is_400_not_transition_conflict(tmp_path):
    store, projects, api = open_api(tmp_path / "state.db")
    projects.register(make_project())
    response = api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(LIFECYCLE_WRITE_SCOPE), idempotency_key="bad-enum", body={"to_state": "NOT_A_STATE", "reason": "bad", "trigger": "OWNER_API"})
    assert response.status_code == 400
    assert response.body["error"]["code"] == "INVALID_REQUEST"
    assert projects.get("P5API").lifecycle_state == ProjectLifecycleState.IDEA
    store.close()


def test_service_mutation_receipt_failure_rolls_back_control_plane_transition(tmp_path):
    class FailingServiceMutationStore(SQLitePersistenceStore):
        def save_service_mutation(self, value):
            raise RuntimeError("forced service mutation persistence failure")
    store = FailingServiceMutationStore(tmp_path / "state.db")
    store.initialize()
    projects = ProjectRegistry(store)
    projects.register(make_project())
    api = ServiceApiV1(projects, store)
    response = api.dispatch("POST", "/api/v1/projects/P5API/lifecycle-transitions", principal=principal(LIFECYCLE_WRITE_SCOPE), idempotency_key="atomic-1", body={"to_state": "ONBOARDING", "reason": "atomic", "trigger": "OWNER_API"})
    assert response.status_code == 500
    assert response.body["error"]["code"] == "INTERNAL_ERROR"
    assert projects.get("P5API").lifecycle_state == ProjectLifecycleState.IDEA
    assert store.list_lifecycle_transitions("P5API") == ()
    assert store.list_audit_events("P5API") == ()
    store.close()
