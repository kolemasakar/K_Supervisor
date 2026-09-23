# SUPPLY_CHAIN_SECURITY

K_Supervisor Phase 6 software supply-chain security and evidence contract.

Version: 1.0
Status: ACTIVE
Date: 2026-09-23
Scope: ROADMAP v0.4 Phase 6

## Trust Boundaries

Pull-request validation is untrusted-code validation and retains read-only repository permissions.

Trusted-main attestation is a separate workflow and is the only Phase 6 CI path granted:

```text
contents: read
id-token: write
attestations: write
```

No package publication permission is granted by the attestation workflow.

## Supported Python and Dependency Resolution

Supported stable Python minors are 3.13 and 3.14. Package metadata is bounded to:

```text
>=3.13,<3.15
```

Protected validation resolves from exact per-minor CI lock files. Python 3.15 is unsupported until separately qualified.

## SBOM Contract

`tools.sbom` generates deterministic SPDX 2.3 JSON from the installed runtime dependency graph.

The SBOM records:

- K_Supervisor package/version;
- runtime dependency packages and versions;
- package purls;
- dependency relationships;
- exact source commit;
- built wheel SHA-256;
- source commit timestamp instead of wall-clock generation time.

Missing runtime dependencies, lock mismatches, invalid commit/digest inputs or invalid SPDX relationships fail closed.

## Vulnerability Evidence

`tools.vulnerability_scan` queries the public OSV package-version API for packages in the SPDX runtime graph.

Machine-readable states are:

```text
CLEAN
EXCEPTIONS_APPLIED
VULNERABLE
UNAVAILABLE
MALFORMED
```

`UNAVAILABLE` and `MALFORMED` are failures, never aliases for `CLEAN`.

The vulnerability exception list is `security/vulnerability_allowlist.json`. Each exception must identify one advisory/package pair and include an expiry date and rationale. The default allowlist is empty.

## Immutable Workflow Dependencies

Every external GitHub Action in active workflows must be pinned to a verified full 40-character commit SHA. Human-readable release/tag names may appear only as comments.

Repository regression tests scan all workflow `uses:` references and reject mutable external refs.

## Trusted-main Attestations

`.github/workflows/supply-chain-attestation.yml` builds the wheel from the exact trusted `main` commit, creates deterministic SBOM/digest evidence, and creates:

- GitHub build-provenance attestation for the wheel;
- GitHub SBOM attestation linking the wheel to the generated SPDX document.

The workflow records attestation URLs and bundles in `supply-chain-evidence.json` and uploads the complete evidence bundle as a workflow artifact.

Attestation proves the trusted build relationship; it does not replace protected tests, vulnerability review, owner release review or publication approval.

## Failure Policy

A Phase 6 candidate is not supply-chain qualified when:

- either supported Python validation fails;
- dependency resolution deviates from the exact lock;
- SBOM generation/validation fails;
- OSV reports an unexcepted advisory;
- OSV evidence is unavailable or malformed;
- an external Action uses a mutable ref;
- trusted-main attestation cannot be produced where the GitHub attestation path is available and required by the audited workflow.

No paid external service is required to satisfy this contract.

## Publication Boundary

Package, Plugin, marketplace/workspace or other external publication remains manual and owner-controlled. Supply-chain automation must never turn successful validation/attestation into automatic publication.
