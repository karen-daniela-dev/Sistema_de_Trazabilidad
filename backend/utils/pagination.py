"""Utilidades de paginación reutilizables."""
from fastapi import Query
from pydantic import BaseModel
from typing import TypeVar, Generic, Sequence

T = TypeVar("T")


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Página (desde 1)"),
        size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    ):
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class Page(BaseModel, Generic[T]):
    items: Sequence[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def build(cls, items: Sequence[T], total: int, params: PaginationParams) -> "Page[T]":
        pages = max(1, -(-total // params.size))  # ceiling division
        return cls(items=items, total=total, page=params.page, size=params.size, pages=pages)
