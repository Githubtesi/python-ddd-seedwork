from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, List, Any

T = TypeVar("T")

@dataclass(frozen=True)
class Result(Generic[T]):
    """
    処理結果をカプセル化するクラス。
    成功・失敗の状態と、データを一貫した形式で返します。
    """
    is_success: bool
    value: Optional[T] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, value: T = None) -> "Result[T]":
        return cls(is_success=True, value=value)

    @classmethod
    def fail(cls, error: str) -> "Result[T]":
        return cls(is_success=False, error=error)

@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    """
    一覧表示（ページネーション）のための結果クラス。
    """
    items: List[T]
    total_count: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return (self.total_count + self.page_size - 1) // self.page_size
