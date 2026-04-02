from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Type, Dict, Any, TypeVar, List
from .command import Command, IUseCase
from .query import Query, IQueryHandler
from .result import Result

@dataclass(frozen=True)
class Identity:
    """
    操作を実行しているユーザーまたはシステムの識別情報を表す値オブジェクト。
    アプリケーション層全体で「誰が」操作しているかを共有するために使用されます。
    """
    id: str
    name: str
    roles: List[str] = field(default_factory=list)

    def is_in_role(self, role: str) -> bool:
        """特定のロールを持っているか確認します。"""
        return role in self.roles


class IIdentityContext(ABC):
    """
    現在の実行コンテキストにおける Identity を取得するためのインターフェース。
    WebフレームワークのセッションやJWTトークンからIdentityを復元する具象クラスの抽象となります。
    """
    @property
    @abstractmethod
    def current_identity(self) -> Identity:
        """現在の Identity を返します。"""
        pass
