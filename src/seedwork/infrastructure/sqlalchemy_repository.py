from abc import abstractmethod
from typing import Any, Generic, List, Optional, Type, TypeVar
import uuid

from sqlalchemy import select, update
from sqlalchemy.orm.exc import StaleDataError
from sqlalchemy.orm import Session

from ..domain.entity import Entity
from ..domain.repository import IRepository

# ドメインエンティティの型
T_Entity = TypeVar("T_Entity", bound=Entity)
# SQLAlchemyのモデル型
T_Model = TypeVar("T_Model")


class SQLAlchemyRepository(IRepository[T_Entity, Any], Generic[T_Entity, T_Model]):
    """
    SQLAlchemy を使用したリポジトリの基底クラス。

    ドメインエンティティと DB モデルの変換ロジックを Infrastructure 層に
    閉じ込め、Domain 層へ SQLAlchemy の型を漏らさないようにします。
    """

    def __init__(self, session: Session, model_type: Type[T_Model]):
        self._session = session
        self._model_type = model_type

    def save(self, entity: T_Entity) -> None:
        """エンティティを DB モデルに変換して Session に登録します。"""
        model = self._to_model(entity)
        self._session.merge(model)

    def find_by_id(self, entity_id: Any) -> Optional[T_Entity]:
        """ID で検索し、DB モデルをドメインエンティティへ変換して返します。"""
        model = self._session.get(self._model_type, entity_id)
        return self._to_domain(model) if model is not None else None

    def delete(self, entity_id: Any) -> None:
        """指定した ID のレコードを削除します。"""
        model = self._session.get(self._model_type, entity_id)
        if model is not None:
            self._session.delete(model)

    def find_all(self) -> List[T_Entity]:
        """全件取得し、ドメインエンティティのリストとして返します。"""
        statement = select(self._model_type)
        models = self._session.scalars(statement).all()
        return [self._to_domain(model) for model in models]

    def next_identity(self) -> str:
        """デフォルトの ID 生成（UUID）です。必要に応じてオーバーライドします。"""
        return str(uuid.uuid4())

    @abstractmethod
    def _to_domain(self, model: T_Model) -> T_Entity:
        """DB モデルからドメインエンティティへの変換ロジック。"""
        raise NotImplementedError

    @abstractmethod
    def _to_model(self, entity: T_Entity) -> T_Model:
        """ドメインエンティティから DB モデルへの変換ロジック。"""
        raise NotImplementedError
