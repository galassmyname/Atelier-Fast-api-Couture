"""Schémas partagés : format des listes paginées."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Liste paginée : {"items": [...], "total": n, "limit": n, "offset": n}."""

    items: list[T]
    total: int
    limit: int
    offset: int
