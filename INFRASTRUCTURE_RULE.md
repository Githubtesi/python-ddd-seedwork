# インフラストラクチャ層選定・実装ガイドライン
## 1. 役割
Infrastructure層は、**Domain層・Application層が定義した抽象を、DBや外部サービス等の具体技術へ接続する層**です。

閉じ込める対象:
- データベース / ORM
- Repositoryの具体実装
- トランザクション
- 認証・実行コンテキストの具体実装
- 外部API / メッセージング / ファイル / キャッシュ
- 技術固有の例外

Infrastructure層に業務ルールを実装してはいけません。

## 2. 参照資料
- `DOMAIN_RULE.md`
- `MODULE_RULE.md`
- `APPLICATION_RULE.md`
- `src/seedwork/domain/` のRepository等の抽象
- `src/seedwork/application/` のUnit of Work / Identity Context等の抽象
- `src/seedwork/infrastructure/` の既存実装

## 3. 部品選定表
| 部品 | 役割 | パス | 対応する抽象 |
| :--- | :--- | :--- | :--- |
| **Database** | DB Engine / Sessionを管理 | `database_setup.py` | SQLAlchemy |
| **Repository Implementation** | Domain Repositoryの永続化を実装 | `sqlalchemy_repository.py` | `IRepository` |
| **Unit of Work Implementation** | DBトランザクションを実装 | `sqlalchemy_unit_of_work.py` | `IUnitOfWork` |
| **Identity Context Implementation** | Identity抽象を実行環境へ接続 | `identity_context_implementation.py` | `IIdentityContext` |
| **Infrastructure Exception** | 技術固有エラーを表現 | `infrastructure_exceptions.py` | `InfrastructureException` |

## 4. 依存方向
InfrastructureはDomain/Applicationの抽象を実装します。

```text
Application
    ↓
DomainのRepository等の抽象
    ↑
Infrastructureの具体実装
    ↓
SQLAlchemy / DB / 外部API
```

内側の層へSQLAlchemy等の具体技術を漏らさないことを基本とします。

## 5. Repository実装
Domainでは保存方法やDB製品を意識せずRepositoryの抽象を定義し、InfrastructureでSQLAlchemy等を実装します。

```text
Domain Entity
     ↓ _to_model()
DB Model

DB Model
     ↓ _to_domain()
Domain Entity
```

### 必須ルール
- Domain EntityとDB Modelを分離する。
- Entity ⇔ DB ModelのMappingをInfrastructure内に閉じ込める。
- SQLAlchemy SessionをDomainへ渡さない。
- DB ModelをDomain層へ漏らさない。
- Repositoryの業務判断をInfrastructureへ実装しない。

## 6. Unit of Work
Applicationは `IUnitOfWork` を利用し、InfrastructureがSQLAlchemy等の具体的トランザクションを実装します。

```text
Application
    ↓
IUnitOfWork
    ↑
SQLAlchemyUnitOfWork
    ↓
SQLAlchemy Session
    ↓
Database
```

基本ライフサイクル:
1. `with unit_of_work:` で開始
2. Repository操作を実行
3. 正常終了ならcommit
4. 例外ならrollback
5. Sessionをclose

## 7. Database
`database_setup.py`の `Database` のように、DB接続・Session生成をInfrastructureへ閉じ込めます。

ApplicationやDomainから `create_engine()`、`sessionmaker()`、`Session()` を直接呼び出さないでください。

DB接続URL等の環境依存値もDomain/Applicationへハードコードしません。

## 8. Identity Context
Applicationは `IIdentityContext` という抽象だけを利用し、Infrastructure / Presentationで実際の認証情報をIdentityへ変換します。

```text
HTTP Request / Test / Batch
          ↓
具体的IdentityContext
          ↓
IIdentityContext
          ↓
Application
```

## 9. Infrastructure Exception
| 例外 | 用途 |
| :--- | :--- |
| `InfrastructureException` | Infrastructure共通例外 |
| `DatabaseConnectionError` | DB接続失敗 |
| `MappingError` | Domain ModelとDB Modelの変換失敗 |

意味を混同しないでください。
- 業務ルール違反 → DomainException
- 入力・権限・未存在等 → AppException
- DB / ORM / 外部サービス等 → InfrastructureException

## 10. 業務ロジック禁止
「金額がマイナスになってはいけない」のような業務ルールをRepositoryやDB Adapterに書かないでください。

```text
Domain
  Money / Order
      ↓
  業務ルールを保証

Infrastructure
  Repository
      ↓
  保存・取得だけを担当
```

## 11. 外部サービス連携
外部API、メール、メッセージング、ストレージ等も同じ原則を適用します。

```text
Application / Domain
        ↓
      抽象
        ↑
Infrastructure Adapter
        ↓
外部API / SDK / DB
```

外部SDKの型をDomainモデルへ直接持ち込まず、必要ならAdapter内で変換します。

## 12. Dependency Injection
具体実装はApplicationへ埋め込まず、外側から注入できる構造を基本とします。

```python
repository = SqlAlchemyMemberRepository(session)
use_case = RegisterMemberUseCase(
    repository=repository,
    unit_of_work=unit_of_work,
)
```

## 13. 配置ルール
`MODULE_RULE.md`に従います。

```text
src/
├── seedwork/infrastructure/  # 共通の基盤実装
├── shared_kernel/
└── features/
    └── member_management/
        ├── domain/
        ├── use_cases/
        ├── infrastructure/  # 機能固有のDB/API実装
        └── presentation/
```

`src/seedwork/infrastructure/`には再利用可能な基盤実装を配置し、Feature固有のRepositoryやDB Modelをseedworkへ追加しないでください。

## 14. 実装チェックリスト
- [ ] 技術的詳細であり、業務ルールではないか
- [ ] Domain/Applicationの抽象を実装しているか
- [ ] SQLAlchemy等の具体技術がDomainへ漏れていないか
- [ ] DB ModelとDomain Entityを分離しているか
- [ ] MappingをInfrastructure内に閉じ込めているか
- [ ] SessionをDomainへ渡していないか
- [ ] TransactionをUnit of Workとして管理しているか
- [ ] DB接続・Session管理をInfrastructure内で行っているか
- [ ] 技術固有エラーをInfrastructure Exceptionとして整理しているか
- [ ] Feature固有実装をseedworkへ追加していないか
- [ ] Dependency Injectionで差し替え可能か
- [ ] 外部SDKの型がDomain/Applicationへ漏れていないか

## 15. AIへの対応手順
### ステップ1：「〇〇のインフラ実装を検討してください」
1. 対応するDomain/Applicationの抽象を特定する。
2. Repository、Unit of Work、Identity Context等の実装対象を決める。
3. 使用技術を決定する。
4. Mapping、Transaction、例外処理を決定する。
5. seedwork / feature infrastructureの配置先を決める。
6. **抽象、具体実装、技術、Mapping、Transaction、例外、DI、配置先**を提示する。

### ステップ2：「提案内容を元にインフラを作成してください」
1. 既存の抽象を確認する。
2. 具体実装をInfrastructureへ追加する。
3. Domain/Applicationへ技術依存を追加しない。
4. MappingとTransaction管理をInfrastructure内で実装する。
5. 技術固有例外を適切に変換する。
6. テストで差し替え可能な構造を維持する。
7. Domain → Application → Infrastructureの責務境界を再確認する。