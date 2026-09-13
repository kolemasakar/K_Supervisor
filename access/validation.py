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


def validate_access_references(value, path: str = "config") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            normalized = str(key).lower()
            if normalized in SENSITIVE_KEYS and not isinstance(item, (dict, list, tuple)):
                if not isinstance(item, str) or not item.startswith("secret://"):
                    raise ValueError(f"raw access data is prohibited at {child}")
            validate_access_references(item, child)
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            validate_access_references(item, f"{path}[{index}]")
