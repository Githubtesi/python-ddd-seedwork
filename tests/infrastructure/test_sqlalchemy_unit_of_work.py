import pytest
from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column

from seedwork.infrastructure.database_setup import Base, Database
from seedwork.infrastructure.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork


class UserModel(Base):
    __tablename__ = "test_users_uow"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


@pytest.fixture
def database():
    db = Database("sqlite:///:memory:")
    db.create_database()
    return db


def test_successful_context_commits(database):
    uow = SQLAlchemyUnitOfWork(database.session_factory)

    with uow:
        uow.session.add(UserModel(id="1", name="Alice"))

    with database.session() as session:
        assert session.get(UserModel, "1").name == "Alice"


def test_exception_context_rolls_back(database):
    uow = SQLAlchemyUnitOfWork(database.session_factory)

    with pytest.raises(RuntimeError):
        with uow:
            uow.session.add(UserModel(id="1", name="Alice"))
            raise RuntimeError("rollback")

    with database.session() as session:
        assert session.get(UserModel, "1") is None


def test_commit_failure_rolls_back_and_closes_session():
    class FailingSession:
        def __init__(self):
            self.rollback_called = False
            self.close_called = False

        def commit(self):
            raise RuntimeError("commit failed")

        def rollback(self):
            self.rollback_called = True

        def close(self):
            self.close_called = True

    factory = lambda: FailingSession()
    uow = SQLAlchemyUnitOfWork(factory)

    with pytest.raises(RuntimeError, match="commit failed"):
        with uow:
            pass

    assert uow._session is None


def test_operations_before_enter_raise_runtime_error(database):
    uow = SQLAlchemyUnitOfWork(database.session_factory)

    with pytest.raises(RuntimeError):
        uow.commit()

    with pytest.raises(RuntimeError):
        uow.rollback()

    with pytest.raises(RuntimeError):
        _ = uow.session
