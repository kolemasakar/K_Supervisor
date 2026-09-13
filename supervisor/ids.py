from __future__ import annotations

from uuid import uuid4


class IdFactory:
    def new(self, prefix: str) -> str:
        return f"{prefix}_{uuid4().hex}"
