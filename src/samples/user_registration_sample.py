import sys
from datetime import datetime
from dataclasses import dataclass

# 本来は別ファイルですが、サンプルとして1ファイルにまとめています
# seedworkのインポートをシミュレート
from seedwork.domain import (
    ValueObject, Entity, AggregateRoot, IRepository, 
    DomainEvent, DomainEventSubscriber, publisher,
    ValueObjectValidationError
)

# ---------------------------------------------------------
# 1. Domain Layer - Value Objects
# ---------------------------------------------------------
@dataclass(frozen=True)
class UserId(ValueObject):
    value: str
    def validate(self):
        if not self.value:
            raise ValueObjectValidationError("ID cannot be empty", "UserId")

@dataclass(frozen=True)
class Email(ValueObject):
    value: str
    def validate(self):
        if "@" not in self.value:
            raise ValueObjectValidationError("Invalid email format", "Email")

# ---------------------------------------------------------
# 2. Domain Layer - Events
# ---------------------------------------------------------
@dataclass(frozen=True)
class UserRegistered(DomainEvent):
    user_name: str
    email: str

# ---------------------------------------------------------
# 3. Domain Layer - Aggregate Root
# ---------------------------------------------------------
@dataclass
class User(AggregateRoot[UserId]):
    name: str
    email: Email

    @classmethod
    def create(cls, user_id: UserId, name: str, email: Email) -> "User":
        user = cls(id=user_id, name=name, email=email)
        # イベントを記録
        user.record_event(UserRegistered(
            aggregate_id=user_id.value,
            user_name=name,
            email=email.value
        ))
        return user

# ---------------------------------------------------------
# 4. Domain Layer - Repository Interface
# ---------------------------------------------------------
class IUserRepository(IRepository[User]):
    # User特有のメソッドが必要なら定義
    pass

# ---------------------------------------------------------
# 5. Infrastructure Layer - Repository Implementation
# ---------------------------------------------------------
class InMemoryUserRepositoryImpl(IUserRepository):
    def __init__(self):
        self._data = {}

    def next_identity(self) -> str:
        import uuid
        return str(uuid.uuid4())

    def save(self, entity: User) -> None:
        self._data[entity.id.value] = entity
        print(f"[DB] User '{entity.name}' を保存しました。")

    def find_by_id(self, entity_id: str) -> User:
        return self._data.get(entity_id)

    def delete(self, entity_id: str) -> None:
        if entity_id in self._data: del self._data[entity_id]

    def find_all(self) -> list[User]:
        return list(self._data.values())

# ---------------------------------------------------------
# 6. Domain Layer - Subscriber (Handler)
# ---------------------------------------------------------
class WelcomeEmailHandler(DomainEventSubscriber):
    @property
    def subscribed_to_type(self):
        return UserRegistered

    def handle(self, event: UserRegistered):
        print(f"[Email] {event.user_name}様 ({event.email}) 宛にウェルカムメールを送信しました！")
        print(f"       (EventID: {event.event_id}, Occurred at: {event.occurred_on})")

# ---------------------------------------------------------
# 7. Application Layer - Service
# ---------------------------------------------------------
class RegisterUserService:
    def __init__(self, repo: IUserRepository):
        self._repo = repo

    def execute(self, name: str, email_str: str):
        print(f"\n--- ユーザー登録開始: {name} ---")
        try:
            # ID生成・値オブジェクト化
            uid = UserId(self._repo.next_identity())
            email = Email(email_str)

            # ドメインロジック実行
            user = User.create(uid, name, email)

            # 保存
            self._repo.save(user)

            # イベント発行
            events = user.pull_events()
            publisher.publish_all(events)
            
            print(f"--- ユーザー登録完了: ID={uid.value} ---\n")
        except ValueObjectValidationError as e:
            print(f"[Error] 入力エラー: {e}")
        except Exception as e:
            print(f"[Error] 予期せぬエラー: {e}")

# ---------------------------------------------------------
# 8. Execution - Running the sample
# ---------------------------------------------------------
if __name__ == "__main__":
    # 初期設定: ハンドラの登録
    publisher.subscribe(WelcomeEmailHandler())

    # 依存性の注入(DI)の真似事
    repo = InMemoryUserRepositoryImpl()
    service = RegisterUserService(repo)

    # 正常系
    service.execute("田中 太郎", "tanaka@example.com")

    # 異常系 (バリデーションエラー)
    service.execute("失敗 ユーザー", "invalid-email")
