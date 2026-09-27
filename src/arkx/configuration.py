"""Canonical, secret-safe configuration identity for reproducible runs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class ConfigurationSnapshot:
    """Reproducibility snapshot without storing secret material."""

    component: str
    version: str
    public_values: Mapping[str, Any]
    secret_digests: Mapping[str, str] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.component.strip() or not self.version.strip():
            raise ValueError("configuration component and version must be non-empty")
        if self.schema_version < 1:
            raise ValueError("configuration schema_version must be positive")
        public = dict(self.public_values)
        secrets = dict(self.secret_digests)
        if any(not str(key).strip() for key in public) or any(not str(key).strip() for key in secrets):
            raise ValueError("configuration keys must be non-empty")
        if any(not str(value).strip() for value in secrets.values()):
            raise ValueError("secret digests must be non-empty")
        object.__setattr__(self, "public_values", public)
        object.__setattr__(self, "secret_digests", secrets)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "component": self.component,
            "version": self.version,
            "public_values": self.public_values,
            "secret_digests": self.secret_digests,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()[:16]

    @property
    def reference(self) -> str:
        return f"config://{self.digest()}"
