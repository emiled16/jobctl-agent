from __future__ import annotations

from typing import TypedDict


class Message(TypedDict, total=False):
    role: str
    content: str


__all__ = ["Message"]
