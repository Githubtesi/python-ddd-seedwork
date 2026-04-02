from abc import ABC, abstractmethod
from typing import Type, Dict, Any, TypeVar
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
