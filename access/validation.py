from __future__ import annotations

SENSITIVE_KEYS = {
    "api_key",
    "access_key",
    "client_secret",
    "credential",
    "credentials",
    "password",
    "private_key",
    "secret",
    "token",
}


def _validate_sensitive_value(value, path: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_sensitive_value(item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_sensitive_value(item, f"{path}[{index}]")
        return
    if not isinstance(value, str) or not value.startswith("secret://"):
        raise ValueError(f"raw access data is prohibited at {path}")


def validate_access_references(value, path: str = "config") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if str(key).lower() in SENSITIVE_KEYS:
                _validate_sensitive_value(item, child)
            else:
                validate_access_references(item, child)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            validate_access_references(item, f"{path}[{index}]")
