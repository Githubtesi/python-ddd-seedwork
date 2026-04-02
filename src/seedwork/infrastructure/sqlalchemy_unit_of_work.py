from typing import Any
from sqlalchemy.orm import Session, sessionmaker
from ..application.unit_of_work import IUnitOfWork

class SQLAlchemyUnitOfWork(IUnitOfWork):
    """
    SQLAlchemy の Session を利用した Unit of Work の実装。
    """
    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory
        self._session: Optional[Session] = None

    def __enter__(self) -> "SQLAlchemyUnitOfWork":
        self._session = self._session_factory()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """例外の有無に応じて自動的に commit/rollback を行い、セッションを閉じます。"""
        try:
            super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            if self._session:
                self._session.close()

    def commit(self) -> None:
        """セッションの変更を確定させます。"""
        if self._session:
            self._session.commit()

    def rollback(self) -> None:
        """セッションの変更を破棄します。"""
        if self._session:
            self._session.rollback()

    @property
    def session(self) -> Session:
        """リポジトリなどが利用するための SQLAlchemy セッション。"""
        if not self._session:
            raise RuntimeError("UnitOfWork が開始されていません。with 構文を使用してください。")
        return self._session
