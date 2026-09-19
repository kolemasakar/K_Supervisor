from __future__ import annotations

import json
import tomllib
from ipaddress import ip_address, ip_network
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from access import AccessReference


_DEFAULT_GROUPS = (
    "k_supervisor.agents",
    "k_supervisor.capabilities",
    "k_supervisor.project_templates",
    "k_supervisor.adapters",
)


class ServicePrincipalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    principal_id: str = Field(min_length=1, max_length=200)
    scopes: tuple[str, ...] = Field(min_length=1)
    token_ref: AccessReference

    @field_validator("principal_id")
    @classmethod
    def validate_principal_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("principal_id must not be empty")
        return value

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(value.strip() for value in values)
        if any(not value for value in normalized):
            raise ValueError("service scopes must not be empty")
        if len(set(normalized)) != len(normalized):
            raise ValueError("service scopes must be unique")
        return normalized


class ServiceExtensionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["agent", "capability", "project_template", "adapter"]
    name: str = Field(min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("extension name must not be empty")
        return value


class ServiceHostConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    bind_host: str = "127.0.0.1"
    port: int = Field(default=8080, ge=0, le=65535)
    workers: int = Field(default=8, ge=1, le=64)
    socket_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    drain_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    proxy_mode: bool = False
    trusted_proxies: tuple[str, ...] = ()
    principals: tuple[ServicePrincipalConfig, ...] = ()
    extensions: tuple[ServiceExtensionConfig, ...] = ()

    @field_validator("bind_host")
    @classmethod
    def validate_bind_host(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("service bind_host must not be empty")
        return value

    @field_validator("trusted_proxies")
    @classmethod
    def validate_trusted_proxies(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        for value in values:
            try:
                ip_network(value, strict=False)
            except ValueError as exc:
                raise ValueError("trusted_proxies must contain IP addresses or CIDRs") from exc
        return values

    @model_validator(mode="after")
    def validate_exposure(self):
        if self.proxy_mode and not self.trusted_proxies:
            raise ValueError("proxy_mode requires at least one trusted proxy")
        loopback = self.bind_host.lower() == "localhost"
        if not loopback:
            try:
                loopback = ip_address(self.bind_host).is_loopback
            except ValueError:
                loopback = False
        if not loopback and not self.proxy_mode:
            raise ValueError("non-loopback service binding requires proxy_mode")
        return self


class ServiceClientConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    base_url: str = "http://127.0.0.1:8080"
    token_ref: AccessReference | None = None
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        value = value.rstrip("/")
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname is None:
            raise ValueError("service client base_url must use http or https")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("service client base_url must not contain credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("service client base_url must not contain query or fragment")
        if parsed.scheme == "http":
            host = parsed.hostname.lower()
            loopback = host == "localhost"
            if not loopback:
                try:
                    loopback = ip_address(host).is_loopback
                except ValueError:
                    loopback = False
            if not loopback:
                raise ValueError("cleartext service client URLs are allowed only on loopback")
        return value


class PlatformConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    config_version: str = "1"
    state_db_path: str = "runtime/k_supervisor.db"
    extension_groups: tuple[str, ...] = Field(default=_DEFAULT_GROUPS, min_length=1)
    strict_extensions: bool = True
    service_host: ServiceHostConfig | None = None
    service_client: ServiceClientConfig | None = None

    @field_validator("config_version")
    @classmethod
    def validate_config_version(cls, value: str) -> str:
        if value != "1":
            raise ValueError("unsupported configuration version")
        return value


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
