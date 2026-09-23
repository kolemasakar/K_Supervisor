# Protected CI dependency locks

These files freeze the zero-cost protected CI/build environment independently for
Python 3.13 and Python 3.14.

- `ci-py313.lock` is consumed only by the Python 3.13 validation job.
- `ci-py314.lock` is consumed only by the Python 3.14 validation job.
- Consumer package metadata remains ranged in `pyproject.toml`.
- CI creates a fresh `.venv-ci`, installs exact versions, and builds the wheel
  with `--no-isolation` so the build backend is also the locked version.
- Binary-only dependency installation avoids an implicit source-build path in
  protected validation.

The current two lock files intentionally contain the same resolved versions because
the validated ARM64 environments resolved the same package set on 2026-09-22.
They remain separate artifacts so a future Python-minor-specific dependency change
is explicit and reviewable.

Hashes are not embedded in this first lock format because Python-minor/platform
wheel hashes differ. Phase 6 supply-chain evidence records exact resolved versions,
artifact SHA-256 and SPDX package relationships separately; lock updates require a
reviewed PR and protected validation on both supported Python minors.
