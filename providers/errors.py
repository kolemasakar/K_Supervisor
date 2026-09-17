from __future__ import annotations


class ProviderExecutionError(RuntimeError):
    """Safe normalized provider failure that may cross the side-effect boundary."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        category: str,
        retryable: bool = False,
        provider_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.category = category
        self.retryable = retryable
        self.provider_code = provider_code

    def __str__(self) -> str:
        return self.message
