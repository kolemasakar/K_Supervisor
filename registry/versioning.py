from __future__ import annotations

import re

_VERSION_RE = re.compile(r"^(0|[1-9]\d*)(?:\.(0|[1-9]\d*))?(?:\.(0|[1-9]\d*))?$")


class VersionConstraintError(ValueError):
    pass


def parse_version(value: str) -> tuple[int, int, int]:
    match = _VERSION_RE.fullmatch(value.strip())
    if not match:
        raise VersionConstraintError(f"invalid numeric semantic version: {value}")
    return tuple(int(part or 0) for part in match.groups())


def _compare(version: tuple[int, int, int], operator: str, target: tuple[int, int, int]) -> bool:
    if operator in {"=", "=="}:
        return version == target
    if operator == ">":
        return version > target
    if operator == ">=":
        return version >= target
    if operator == "<":
        return version < target
    if operator == "<=":
        return version <= target
    raise VersionConstraintError(f"unsupported version operator: {operator}")


def _caret_upper(version: tuple[int, int, int]) -> tuple[int, int, int]:
    major, minor, patch = version
    if major:
        return major + 1, 0, 0
    if minor:
        return 0, minor + 1, 0
    return 0, 0, patch + 1


def _tilde_upper(version: tuple[int, int, int]) -> tuple[int, int, int]:
    major, minor, _ = version
    return major, minor + 1, 0


def matches_version(version_value: str, constraint: str) -> bool:
    version = parse_version(version_value)
    expression = constraint.strip()
    if expression in {"", "*"}:
        return True
    if expression.startswith("^"):
        lower = parse_version(expression[1:])
        return version >= lower and version < _caret_upper(lower)
    if expression.startswith("~"):
        lower = parse_version(expression[1:])
        return version >= lower and version < _tilde_upper(lower)

    clauses = [item.strip() for item in expression.split(",") if item.strip()]
    for clause in clauses:
        match = re.fullmatch(r"(>=|<=|==|=|>|<)?\s*(\d+(?:\.\d+){0,2})", clause)
        if not match:
            raise VersionConstraintError(f"invalid version constraint: {constraint}")
        operator = match.group(1) or "=="
        if not _compare(version, operator, parse_version(match.group(2))):
            return False
    return True
