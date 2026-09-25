# アプリケーション層選定・実装ガイドライン
## 1. 役割
アプリケーション層は、**ユースケースの手順を調整する層**です。Domainが「何が正しいか」を表現するのに対し、Applicationは「そのルールを使って、何をどの順番で実行するか」を表現します。

必ず以下を分離してください。
- **Domain**: 業務ルール、不変条件、業務上の判断
- **Application**: ユースケース、入出力、トランザクション、処理順序の調整
- **Infrastructure**: DB、ORM、外部API、技術固有の実装

Application層へ業務ルールを移してはいけません。業務ルールはDomain層のEntity、Value Object、Domain Service、Policy、Specification等へ配置してください。

## 2. 参照資料
- `DOMAIN_RULE.md`
- `MODULE_RULE.md`
- `src/seedwork/application/` の基底クラス

## 3. 部品選定表
| 部品 | 役割 | パス | 基底クラス・IF |
| :--- | :--- | :--- | :--- |
| **ApplicationService** | 複数のドメイン処理を調整し、イベント配送等を管理 | `application_service.py` | `ApplicationService` |
| **Command** | 状態変更の意図を表す入力DTO | `command.py` / `messaging.py` | `Command` |
| **Query** | 状態を変更せずデータ取得を要求 | `query.py` / `messaging.py` | `Query` |
| **Use Case** | 1つのユースケースを実行 | `command.py` / `messaging.py` | `IUseCase` |
| **Query Handler** | Queryを処理しDTO等を返す | `query.py` / `messaging.py` | `IQueryHandler` |
| **DTO** | 層をまたぐデータ転送 | `dto.py` | `DTO` |
| **Result** | 成功・失敗を表現 | `result.py` | `Result` |
| **Application Exception** | 入力・権限・未存在等のアプリケーションエラー | `app_exception.py` | `AppException` |
| **Identity** | 現在の利用者・実行主体 | `identity.py` | `Identity` |
| **Identity Context** | 実行主体取得の抽象 | `identity.py` | `IIdentityContext` |
| **Command / Query Bus** | メッセージを対応する処理へ配送 | `bus.py` | `ICommandBus`, `IQueryBus` |
| **Unit of Work** | 複数Repository操作を1トランザクションとして管理 | `unit_of_work.py` | `IUnitOfWork` |

## 4. ユースケース選定フロー
1. 状態変更か読み取りかを判断する。
   - 状態変更 → **Command**
   - 読み取り → **Query**
2. 1つのユーザー操作・業務操作を1つのUse Caseとして定義する。
3. Use CaseからDomainモデルを呼び出して業務ルールを実行する。
4. Repository等の抽象を利用して取得・保存する。
5. 必要に応じてUnit of Workでトランザクションを管理する。
6. AggregateからDomain Eventを回収し、必要に応じてPublishする。
7. DTO / Resultとして結果を返す。

## 5. Command / Queryのルール
Commandは「状態を変更したい」という**意図**だけを表し、業務ロジックを持たせません。

Queryは「情報を取得したい」という**意図**を表し、原則として状態を変更しません。

```python
@dataclass(frozen=True)
class RegisterMemberCommand(Command):
    member_id: str
    name: str
```

## 6. Application Service / Use Caseのルール
Use Caseは**オーケストレーター**として実装します。

```text
Command
  ↓
Use Case / Application Service
  ↓
RepositoryからAggregateを取得
  ↓
Domainのメソッドを呼び出す
  ↓
Repositoryへ保存
  ↓
Unit of Workでcommit
  ↓
Domain Eventをpublish
  ↓
Result / DTO
```

### 禁止事項
- Application Serviceへ業務ルールを書かない。
- Entityの属性を直接変更しない。
- SQLを直接実行しない。
- SQLAlchemy等の具体的Infrastructure実装へ直接依存しない。
- Domain Exceptionと同じ意味の判定をApplication側へ重複実装しない。

## 7. DTO / Result
- DTOは入出力のデータ構造として利用する。
- DTOは原則 `@dataclass(frozen=True)` とする。
- Entityそのものを外部へ直接公開しない。
- Resultを利用する場合は `Result.ok(...)` / `Result.fail(...)` で成功・失敗を明示する。

## 8. 例外
| 例外 | 用途 |
| :--- | :--- |
| `AppException` | Application層の共通例外 |
| `ValidationError` | 入力値・要求内容の不備 |
| `AuthorizationError` | 権限不足 |
| `ResourceNotFoundError` | 指定リソースが存在しない |

業務ルール違反はDomain Exception、DB接続等の技術エラーはInfrastructure Exceptionへ分離します。

## 9. Identity
Application層は `IIdentityContext` という抽象を利用し、HTTPやFastAPI等の具体技術を直接参照しません。

```text
Presentation / Infrastructure
        ↓
IIdentityContext
        ↓
Application Use Case
```

## 10. Unit of Work
複数Repository操作を1トランザクションとして扱う場合は `IUnitOfWork` を利用します。

```python
with unit_of_work:
    # Repository操作
    # Domain処理
    ...
# 正常終了 → commit
# 例外発生 → rollback
```

具体的なDBトランザクションはInfrastructure層に実装し、Applicationは抽象に依存します。

## 11. Domain Event
Aggregateが発生させたDomain EventをApplication Serviceが回収し、Publisherへ渡すことができます。Application層でイベントの業務的意味を再実装しないでください。

## 12. 配置ルール
`MODULE_RULE.md`に従い、機能固有のUse Caseは垂直スライスへ配置します。

```text
src/
├── seedwork/application/     # 共通基盤
├── shared_kernel/
└── features/
    └── member_management/
        ├── domain/
        ├── use_cases/        # Application層
        ├── infrastructure/
        └── presentation/
```

## 13. 実装チェックリスト
- [ ] これはユースケースの手順であり、業務ルールではないか
- [ ] 状態変更ならCommand、読み取りならQueryか
- [ ] 1つの操作に対して責務が明確か
- [ ] Domainに任せる判断をApplicationへ書いていないか
- [ ] Entityの状態を直接変更していないか
- [ ] Repositoryの具体実装へ依存していないか
- [ ] 必要なトランザクション境界をUnit of Workで表現しているか
- [ ] Domain Eventを適切なタイミングでPublishしているか
- [ ] DTO / Resultで入出力を整理しているか

## 14. AIへの対応手順
### ステップ1：「〇〇のユースケースを検討してください」
1. Command / Queryを判断する。
2. 必要なDomainモデルを特定する。
3. Repository、Unit of Work、Identity Context等の抽象を特定する。
4. 処理順序を提案する。
5. **ユースケース名、種別、入力、Domainモデル、Repository、トランザクション、出力、エラーケース**を提示する。

### ステップ2：「提案内容を元にユースケースを作成してください」
1. 合意した処理順序に基づいて実装する。
2. Domainの業務ルールをApplicationへコピーしない。
3. Infrastructureの具体実装ではなく抽象へ依存する。
4. 必要に応じてDomain EventをPublishする。
5. 正常系・異常系のResultまたはApplication Exceptionを明確にする。