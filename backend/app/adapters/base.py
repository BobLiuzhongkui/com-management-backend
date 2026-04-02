"""
Abstract Adapter layer for external integrations.
Define interfaces here to keep business logic decoupled from specific providers.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """All adapters must implement this interface."""

    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Example: Third-party communication provider adapter
# ---------------------------------------------------------------------------

class CommProviderAdapter(BaseAdapter):
    """Adapter interface for external communication providers (e.g. Twilio, Plivo, etc.)."""

    @abstractmethod
    async def send_sms(self, to: str, body: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_status(self, message_id: str) -> dict[str, Any]:
        raise NotImplementedError
