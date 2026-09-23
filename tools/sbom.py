from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

NOASSERTION = "NOASSERTION"
SPDX_VERSION = "SPDX-2.3"
DATA_LICENSE = "CC0-1.0"


@dataclass(frozen=True)
class ResolvedPackage:
    name: str
    version: str
    requires: tuple[str, ...] = ()


def parse_lock(path: str | Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise ValueError(f"non-exact lock entry: {line}")
        name, version = line.split("==", 1)
        key = canonicalize_name(name.strip())
        if not key or not version.strip():
            raise ValueError(f"invalid lock entry: {line}")
        if key in result:
            raise ValueError(f"duplicate lock entry: {key}")
        result[key] = version.strip()
    if not result:
        raise ValueError("lock file is empty")
    return result


def _spdx_id(name: str) -> str:
    token = "".join(ch if ch.isalnum() else "-" for ch in canonicalize_name(name))
    token = "-".join(part for part in token.split("-") if part)
    return f"SPDXRef-Package-{token or 'unknown'}"


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _created_from_epoch(source_timestamp: int) -> str:
    if source_timestamp < 0:
        raise ValueError("source timestamp must be non-negative")
    return (
        datetime.fromtimestamp(source_timestamp, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _active_requirements(requirements: tuple[str, ...]) -> tuple[str, ...]:
    active: list[str] = []
    for raw in requirements:
        requirement = Requirement(raw)
        if requirement.marker is not None and not requirement.marker.evaluate():
            continue
        active.append(canonicalize_name(requirement.name))
    return tuple(sorted(dict.fromkeys(active)))


def collect_runtime_graph(root_distribution: str) -> dict[str, ResolvedPackage]:
    distributions = {
        canonicalize_name(dist.metadata["Name"]): dist
        for dist in importlib.metadata.distributions()
        if dist.metadata.get("Name")
    }
    root = canonicalize_name(root_distribution)
    if root not in distributions:
        raise RuntimeError(f"installed root distribution not found: {root_distribution}")

    queue = [root]
    packages: dict[str, ResolvedPackage] = {}
    while queue:
        name = queue.pop(0)
        if name in packages:
            continue
        dist = distributions.get(name)
        if dist is None:
            raise RuntimeError(f"installed runtime dependency not found: {name}")
        requires = _active_requirements(tuple(dist.requires or ()))
        packages[name] = ResolvedPackage(
            name=dist.metadata["Name"],
            version=dist.version,
            requires=requires,
        )
        for dependency in requires:
            if dependency not in packages:
                queue.append(dependency)
    return packages


def verify_locked_runtime(
    packages: dict[str, ResolvedPackage],
    lock: dict[str, str],
    *,
    root_distribution: str,
) -> None:
    root = canonicalize_name(root_distribution)
    for name, package in sorted(packages.items()):
        if name == root:
            continue
        expected = lock.get(name)
        if expected is None:
            raise RuntimeError(f"runtime dependency missing from lock: {name}")
        if package.version != expected:
            raise RuntimeError(
                f"runtime dependency lock mismatch for {name}: "
                f"expected {expected}, got {package.version}"
            )


def build_spdx_document(
    *,
    packages: dict[str, ResolvedPackage],
    root_distribution: str,
    wheel_sha256: str,
    repository: str,
    commit: str,
    source_timestamp: int,
) -> dict:
    root = canonicalize_name(root_distribution)
    if root not in packages:
        raise ValueError("root distribution is absent from runtime package graph")
    if len(commit) != 40 or any(ch not in "0123456789abcdefABCDEF" for ch in commit):
        raise ValueError("commit must be a full 40-character hexadecimal SHA")
    if len(wheel_sha256) != 64:
        raise ValueError("wheel_sha256 must be a 64-character SHA-256 digest")

    root_package = packages[root]
    namespace = (
        repository.rstrip("/")
        + "/spdx/"
        + commit.lower()
        + "/"
        + wheel_sha256.lower()
    )
    spdx_packages = []
    relationships = []

    for canonical_name, package in sorted(packages.items()):
        spdx_id = _spdx_id(canonical_name)
        item = {
            "SPDXID": spdx_id,
            "name": package.name,
            "versionInfo": package.version,
            "downloadLocation": NOASSERTION,
            "filesAnalyzed": False,
            "licenseConcluded": NOASSERTION,
            "licenseDeclared": NOASSERTION,
            "copyrightText": NOASSERTION,
            "externalRefs": [{
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": f"pkg:pypi/{canonical_name}@{package.version}",
            }],
        }
        if canonical_name == root:
            item["checksums"] = [{
                "algorithm": "SHA256",
                "checksumValue": wheel_sha256.lower(),
            }]
            item["sourceInfo"] = f"git+{repository}@{commit.lower()}"
        spdx_packages.append(item)

        for dependency in package.requires:
            if dependency not in packages:
                raise ValueError(
                    f"dependency {dependency} referenced by {canonical_name} "
                    "is absent from the runtime graph"
                )
            relationships.append({
                "spdxElementId": spdx_id,
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": _spdx_id(dependency),
            })

    relationships.append({
        "spdxElementId": "SPDXRef-DOCUMENT",
        "relationshipType": "DESCRIBES",
        "relatedSpdxElement": _spdx_id(root),
    })

    return {
        "spdxVersion": SPDX_VERSION,
        "dataLicense": DATA_LICENSE,
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{root_package.name}-{root_package.version}",
        "documentNamespace": namespace,
        "creationInfo": {
            "created": _created_from_epoch(source_timestamp),
            "creators": ["Tool: K_Supervisor Phase 6 SPDX Generator"],
        },
        "packages": spdx_packages,
        "relationships": sorted(
            relationships,
            key=lambda item: (
                item["spdxElementId"],
                item["relationshipType"],
                item["relatedSpdxElement"],
            ),
        ),
    }


def validate_spdx_document(document: dict, *, root_distribution: str) -> None:
    required = {
        "spdxVersion", "dataLicense", "SPDXID", "name",
        "documentNamespace", "creationInfo", "packages", "relationships",
    }
    missing = required - document.keys()
    if missing:
        raise ValueError("SPDX document missing fields: " + ", ".join(sorted(missing)))
    if document["spdxVersion"] != SPDX_VERSION:
        raise ValueError("unexpected SPDX version")
    if document["dataLicense"] != DATA_LICENSE:
        raise ValueError("unexpected SPDX data license")
    if not document["packages"]:
        raise ValueError("SPDX document contains no packages")

    ids = {item["SPDXID"] for item in document["packages"]}
    root_id = _spdx_id(root_distribution)
    if root_id not in ids:
        raise ValueError("SPDX root package is missing")
    for relationship in document["relationships"]:
        if (
            relationship["spdxElementId"] != "SPDXRef-DOCUMENT"
            and relationship["spdxElementId"] not in ids
        ):
            raise ValueError("SPDX relationship source is missing")
        if relationship["relatedSpdxElement"] not in ids:
            raise ValueError("SPDX relationship target is missing")


def write_spdx_document(document: dict, output: str | Path) -> None:
    Path(output).write_text(
        json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def generate(
    *,
    wheel: str | Path,
    lock_file: str | Path,
    repository: str,
    commit: str,
    source_timestamp: int,
    output: str | Path,
    root_distribution: str = "k-supervisor",
) -> dict:
    packages = collect_runtime_graph(root_distribution)
    lock = parse_lock(lock_file)
    verify_locked_runtime(packages, lock, root_distribution=root_distribution)
    document = build_spdx_document(
        packages=packages,
        root_distribution=root_distribution,
        wheel_sha256=_sha256(wheel),
        repository=repository,
        commit=commit,
        source_timestamp=source_timestamp,
    )
    validate_spdx_document(document, root_distribution=root_distribution)
    write_spdx_document(document, output)
    return document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic SPDX 2.3 SBOM.")
    parser.add_argument("--wheel", required=True)
    parser.add_argument("--lock-file", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--source-timestamp", required=True, type=int)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    generate(
        wheel=args.wheel,
        lock_file=args.lock_file,
        repository=args.repository,
        commit=args.commit,
        source_timestamp=args.source_timestamp,
        output=args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
