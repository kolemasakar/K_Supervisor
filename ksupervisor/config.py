from __future__ import annotations

import json
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


_DEFAULT_GROUPS = (
    "k_supervisor.agents",
    "k_supervisor.capabilities",
    "k_supervisor.project_templates",
    "k_supervisor.adapters",
)


class PlatformConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    config_version: str = "1"
    state_db_path: str = "runtime/k_supervisor.db"
    extension_groups: tuple[str, ...] = Field(default=_DEFAULT_GROUPS, min_length=1)
    strict_extensions: bool = True


def load_config(path: str | Path) -> PlatformConfig:
    source = Path(path)
    raw = source.read_bytes()
    if source.suffix.lower() == ".toml":
        data = tomllib.loads(raw.decode("utf-8"))
    elif source.suffix.lower() == ".json":
        data = json.loads(raw.decode("utf-8"))
    else:
        raise ValueError("configuration must use .json or .toml")
    return PlatformConfig.model_validate(data)
