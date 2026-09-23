import hashlib
import json

import pytest

from tools.sbom import (
    NOASSERTION,
    ResolvedPackage,
    build_spdx_document,
    parse_lock,
    validate_spdx_document,
    verify_locked_runtime,
    write_spdx_document,
)

COMMIT = "a" * 40
WHEEL_SHA = hashlib.sha256(b"wheel-bytes").hexdigest()


def _packages():
    return {
        "k-supervisor": ResolvedPackage(
            "k-supervisor", "0.1.0", ("pydantic",)
        ),
        "pydantic": ResolvedPackage(
            "pydantic", "2.13.5", ("annotated-types",)
        ),
        "annotated-types": ResolvedPackage(
            "annotated-types", "0.8.0", ()
        ),
    }


def test_parse_lock_requires_exact_unique_versions(tmp_path):
    lock = tmp_path / "ci.lock"
    lock.write_text(
        "# comment\nPydantic==2.13.5\nannotated_types==0.8.0\n",
        encoding="utf-8",
    )
    assert parse_lock(lock) == {
        "annotated-types": "0.8.0",
        "pydantic": "2.13.5",
    }

    lock.write_text("pydantic>=2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-exact"):
        parse_lock(lock)


def test_verify_locked_runtime_rejects_different_dependency_version():
    packages = _packages()
    verify_locked_runtime(
        packages,
        {"pydantic": "2.13.5", "annotated-types": "0.8.0"},
        root_distribution="k-supervisor",
    )
    with pytest.raises(RuntimeError, match="lock mismatch"):
        verify_locked_runtime(
            packages,
            {"pydantic": "2.13.4", "annotated-types": "0.8.0"},
            root_distribution="k-supervisor",
        )


def test_spdx_document_is_deterministic_and_contains_required_evidence(tmp_path):
    kwargs = {
        "packages": _packages(),
        "root_distribution": "k-supervisor",
        "wheel_sha256": WHEEL_SHA,
        "repository": "https://github.com/kolemasakar/K_Supervisor",
        "commit": COMMIT,
        "source_timestamp": 1_795_555_200,
    }
    first = build_spdx_document(**kwargs)
    second = build_spdx_document(**kwargs)
    assert first == second
    validate_spdx_document(first, root_distribution="k-supervisor")

    root = next(
        item for item in first["packages"]
        if item["SPDXID"] == "SPDXRef-Package-k-supervisor"
    )
    assert root["checksums"] == [
        {"algorithm": "SHA256", "checksumValue": WHEEL_SHA}
    ]
    assert root["sourceInfo"].endswith("@" + COMMIT)
    assert root["downloadLocation"] == NOASSERTION
    assert root["licenseDeclared"] == NOASSERTION
    assert root["externalRefs"][0]["referenceLocator"] == (
        "pkg:pypi/k-supervisor@0.1.0"
    )
    assert first["creationInfo"]["created"].endswith("Z")
    assert COMMIT in first["documentNamespace"]
    assert WHEEL_SHA in first["documentNamespace"]

    output = tmp_path / "sbom.spdx.json"
    write_spdx_document(first, output)
    payload = output.read_bytes()
    assert payload.endswith(b"\n")
    assert json.loads(payload) == first


def test_spdx_document_rejects_non_full_commit_sha():
    with pytest.raises(ValueError, match="full 40-character"):
        build_spdx_document(
            packages=_packages(),
            root_distribution="k-supervisor",
            wheel_sha256=WHEEL_SHA,
            repository="https://github.com/kolemasakar/K_Supervisor",
            commit="abc123",
            source_timestamp=0,
        )


def test_spdx_failure_paths_fail_closed(tmp_path):
    lock = tmp_path / "ci.lock"
    lock.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        parse_lock(lock)

    lock.write_text("pydantic==2.13.5\nPydantic==2.13.5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        parse_lock(lock)

    packages = _packages()
    with pytest.raises(RuntimeError, match="missing from lock"):
        verify_locked_runtime(
            packages,
            {"pydantic": "2.13.5"},
            root_distribution="k-supervisor",
        )

    with pytest.raises(ValueError, match="root distribution"):
        build_spdx_document(
            packages={"pydantic": packages["pydantic"]},
            root_distribution="k-supervisor",
            wheel_sha256=WHEEL_SHA,
            repository="https://github.com/kolemasakar/K_Supervisor",
            commit=COMMIT,
            source_timestamp=0,
        )

    broken = dict(packages)
    broken["pydantic"] = ResolvedPackage("pydantic", "2.13.5", ("missing-dependency",))
    with pytest.raises(ValueError, match="absent from the runtime graph"):
        build_spdx_document(
            packages=broken,
            root_distribution="k-supervisor",
            wheel_sha256=WHEEL_SHA,
            repository="https://github.com/kolemasakar/K_Supervisor",
            commit=COMMIT,
            source_timestamp=0,
        )


def test_spdx_validation_rejects_incomplete_and_invalid_relationships():
    document = build_spdx_document(
        packages=_packages(),
        root_distribution="k-supervisor",
        wheel_sha256=WHEEL_SHA,
        repository="https://github.com/kolemasakar/K_Supervisor",
        commit=COMMIT,
        source_timestamp=0,
    )

    incomplete = dict(document)
    incomplete.pop("packages")
    with pytest.raises(ValueError, match="missing fields"):
        validate_spdx_document(incomplete, root_distribution="k-supervisor")

    wrong = json.loads(json.dumps(document))
    wrong["relationships"][0]["relatedSpdxElement"] = "SPDXRef-Package-missing"
    with pytest.raises(ValueError, match="target is missing"):
        validate_spdx_document(wrong, root_distribution="k-supervisor")
