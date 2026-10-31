"""
SubscriptIQ Standardized Pagination Models & Helpers.
All list endpoints return { "items": [...], "total": 0, "page": 1, "page_size": 20 }.
"""
from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int

    @classmethod
    def create(cls, items: List[T], total: int, params: PageParams):
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size
        )


PaginatedResponse = PageResponse

