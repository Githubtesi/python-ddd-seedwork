from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Type, Dict, Any, TypeVar, List
from .command import Command, IUseCase
from .query import Query, IQueryHandler
from .result import Result

T_Result = TypeVar("T_Result")

class ICommandBus(ABC):
    """
    コマンドを適切なユースケース（ハンドラ）へ配送するバスのインターフェース。
    """
    @abstractmethod
    def dispatch(self, command: Command) -> Result[Any]:
        pass

class IQueryBus(ABC):
    """
    クエリを適切なクエリハンドラへ配送するバスのインターフェース。
    """
    @abstractmethod
    def ask(self, query: Query) -> Any:
        pass

class InMemoryBus(ICommandBus, IQueryBus):
    """
    インメモリでのシンプルなバス実装。
    """
    def __init__(self):
        self._command_handlers: Dict[Type[Command], IUseCase] = {}
        self._query_handlers: Dict[Type[Query], IQueryHandler] = {}

    def register_command_handler(self, command_type: Type[Command], handler: IUseCase):
        self._command_handlers[command_type] = handler

    def register_query_handler(self, query_type: Type[Query], handler: IQueryHandler):
        self._query_handlers[query_type] = handler

    def dispatch(self, command: Command) -> Result[Any]:
        handler = self._command_handlers.get(type(command))
        if not handler:
            raise ValueError(f"No handler registered for {type(command)}")
        return handler.execute(command)

    def ask(self, query: Query) -> Any:
        handler = self._query_handlers.get(type(query))
        if not handler:
            raise ValueError(f"No handler registered for {type(query)}")
        return handler.handle(query)

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
