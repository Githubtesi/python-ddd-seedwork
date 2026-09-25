# アーキテクチャ設計・実装ガイドライン

## 1. 目的

本ドキュメントは、プロジェクト全体のアーキテクチャ、依存方向、レイヤー境界、モジュール境界を定義する。

個々のレイヤーの詳細な設計ルールは、以下のドキュメントで定義する。

- `DOMAIN_RULE.md`
- `APPLICATION_RULE.md`
- `INFRASTRUCTURE_RULE.md`
- `MODULE_RULE.md`

本ドキュメントは、それらのルールより上位に位置する**プロジェクト全体のアーキテクチャルール**として扱う。

---

## 2. アーキテクチャの基本方針

本プロジェクトでは、DDDとVertical Slice Architecture（VSA）を基本とする。

基本的な責務分離は以下の通り。

Presentation
     ↓
Application
     ↓
Domain

Infrastructure
     ↓
Domain / Application の抽象

各層は、自分より内側の責務を利用できるが、内側の層が外側の具体技術へ依存してはいけない。

基本原則は以下とする。

1. Domainは業務知識の中心とする。
2. Applicationはユースケースの手順を調整する。
3. Infrastructureは技術的な具体実装を担当する。
4. Presentationは外部との入出力を担当する。
5. Featureは業務機能単位で垂直に分割する。
6. SeedworkはDDD実装のための汎用基盤とする。
7. Shared Kernelは複数Featureで共有する業務概念を配置する。
8. Feature間の直接依存を避ける。
9. 依存方向を明確にし、技術詳細を内側へ漏らさない。

---

## 3. レイヤー構成

### 3.1 Domain
Domainは、システムが扱う業務上の意味、ルール、不変条件を表現する。

配置例:
features/member_management/domain

Domainに配置する代表的な要素:
- Entity
- Value Object
- Aggregate Root
- Domain Event
- Domain Service
- Specification
- Factory
- Policy
- Repositoryの抽象

詳細は `DOMAIN_RULE.md` に従う。

### 3.2 Application
Applicationは、ユーザー操作やシステム上のユースケースを実行するための手順を調整する。

配置例:
features/member_management/use_cases

Applicationに配置する代表的な要素:
- Use Case
- Application Service
- Command
- Query
- Query Handler
- DTO
- Result
- Unit of Workの利用
- Identity Contextの利用

ApplicationはDomainの業務ルールを再実装してはいけない。

詳細は `APPLICATION_RULE.md` に従う。

### 3.3 Infrastructure
Infrastructureは、Domain / Applicationが定義した抽象を具体的な技術へ接続する。

代表例:
- Database
- ORM
- Repositoryの具体実装
- Unit of Workの具体実装
- 外部API Adapter
- Message Broker Adapter
- File Storage
- Cache
- Identity Contextの具体実装
- 技術固有例外

共通して再利用する基盤実装は `src/seedwork/infrastructure/` に配置する。
Feature固有は `features/.../infrastructure/`。

詳細は `INFRASTRUCTURE_RULE.md` に従う。

### 3.4 Presentation
Presentationは、外部世界との入出力を担当する。
代表例:
- HTTP API
- CLI
- Web UI Adapter
- Controller
- Request / Response変換

基本:
HTTP Request -> Presentation -> Command / Query -> Application -> Domain

Presentationに業務ルールを実装してはいけない。

---

## 4. 依存方向

### 4.1 基本ルール
Presentation -> Application -> Domain
Infrastructure -> Domain / Applicationの抽象

Infrastructureは外側から具体実装を提供する。

### 4.2 許可される依存
| From | To | 判定 |
|---|---|---|
| Presentation | Application | ○ |
| Application | Domain | ○ |
| Infrastructure | Domain | ○ |
| Infrastructure | Applicationの抽象 | ○ |
| Feature | Seedwork | ○ |
| Feature | Shared Kernel | ○ |

### 4.3 禁止される依存
| From | To | 判定 |
|---|---|---|
| Domain | Application | × |
| Domain | Infrastructure | × |
| Domain | Presentation | × |
| Application | Infrastructureの具体実装 | × |
| Application | Presentation | × |
| Seedwork | Feature | × |
| Seedwork | Shared Kernel | × |
| Shared Kernel | Feature | × |
| Feature A | Feature B | × |

---

## 5. 依存性逆転

Infrastructureなどの外側の具体実装をApplication / Domainから直接参照してはいけない。

Repository:
Domain -> IRepository <- Infrastructure -> SQLAlchemy

DomainはRepository等の抽象を定義し、Infrastructureが具体実装する。
これによりDomain / ApplicationはSQLAlchemy等の技術に依存しない。

---

## 6. 技術依存の境界

以下の具体技術はInfrastructureへ閉じ込める:
- SQLAlchemy
- Database Driver
- HTTP Client
- 外部API SDK
- Message Broker SDK
- Cloud SDK
- File System API
- Cache Client
- Authentication Framework

DomainからSQLAlchemyをimportしてはいけない。
ApplicationからSQLAlchemy Session等を直接利用してはいけない。
ApplicationはRepositoryやUnit of Work等の抽象を利用する。

---

## 7. Domain Modelと永続化モデルの分離

Domain EntityとDatabase Modelは別物として扱う。

Domain Entity -> Mapping -> Database Model -> SQLAlchemy
逆方向も同様。

MappingはInfrastructureに閉じ込める。
Domain EntityにSQLAlchemy Modelを直接保持させない。
Domain EntityからSQLAlchemy Sessionを直接利用しない。

---

## 8. Seedworkの境界

`src/seedwork/` はDDD実装のための汎用基盤。

配置してよい:
- Entity基底クラス
- Value Object基底クラス
- Aggregate Root基底クラス
- Repository抽象
- Domain Event基盤
- Application Service基底クラス
- Command / Query基盤
- Unit of Work抽象
- Infrastructure共通基盤

配置してはいけない:
- Member
- Order
- Invoice
- Customer
- Product
など特定業務機能のモデル。

---

## 9. Shared Kernelの境界

`src/shared_kernel/` は複数Featureで共有する具体的な業務概念を配置。

Feature A -> Shared Kernel <- Feature B

Shared KernelはFeatureへ依存しない。
特定Feature専用の業務ロジックをShared Kernelへ追加しない。
「共有したい」だけで移動せず、複数Featureにまたがる明確な共有責務がある場合のみ検討。

---

## 10. Feature境界

VSAを採用。

src/
├── seedwork/
├── shared_kernel/
└── features/
    ├── member_management/
    ├── order_management/
    └── ...

各Featureは可能な限り自己完結。
feature/
├── domain/
├── use_cases/
├── infrastructure/
└── presentation/

Feature AからFeature Bの内部モデルを直接参照しない。
別Feature連携は原則:
1. ID
2. Domain Event
3. Shared Kernel
4. 必要に応じた明示的Application境界

---

## 11. Feature間連携

内部モデルを直接公開しない。
例:
Order Feature -> Member ID -> Member Feature

またはDomain Event:
Member Feature -> MemberRegistered -> Subscriber in another feature

Feature間の直接importで内部構造を共有しない。

---

## 12. 業務ルールの配置

Domain: 「何が正しいか」
Application: 「何をどの順番で実行するか」
Infrastructure: 「どの技術を使って実現するか」
Presentation: 「外部からどう受け取り、どう返すか」

迷った場合はこの4つの問いを使う。

---

## 13. トランザクション境界

業務的なトランザクション境界はApplicationが調整し、具体的DBトランザクションはInfrastructureが実装。

Application -> IUnitOfWork <- Infrastructure -> SQLAlchemy Session

Applicationは `with unit_of_work:` のように抽象を利用する。

---

## 14. Domain Eventの境界

Domain Eventの「何が起きたか」はDomainが定義。
発行・配送の調整はApplication。
Message Broker等の具体技術はInfrastructure。

---

## 15. Identityの境界

HTTP / Batch / Test -> Concrete Identity Context -> IIdentityContext -> Application

Application / DomainからFastAPI、HTTP Request等の具体オブジェクトを直接参照しない。

---

## 16. 配置判断フロー

① DDD実装の汎用基盤か? -> Seedwork
② 複数Featureで共有する具体的業務概念か? -> Shared Kernel
③ 特定Featureの業務知識か? -> Feature / Domain
④ ユースケースの手順・調整か? -> Feature / Application
⑤ DB・外部API・SDK等の具体技術か? -> Feature / Infrastructure
⑥ HTTP/API/UI等の外部接続か? -> Feature / Presentation

---

## 17. AIによる実装時の対応手順

AIはコード作成・変更前に:
1. Architecture Rule確認
2. MODULE_RULE確認
3. Layer判断
4. 該当Layer Rule確認
5. 既存コード確認
6. 依存方向確認
7. 実装
8. 最終確認

既存の抽象、基底クラス、Repository、Domain Event、Unit of Work、Feature、Mapping、依存関係を確認し、既存設計と矛盾する新しい仕組みを勝手に追加しない。

最終確認:
- Layer依存方向
- Domainへの技術依存漏れ
- Applicationへの業務ルール漏れ
- Infrastructureへの業務ルール漏れ
- Presentationへの業務ルール漏れ
- Feature間直接依存
- SeedworkへのFeature固有コード追加
- Shared Kernelへの不要なFeature固有コード追加
- Domain Entity / DB Model分離
- 外部SDK型の漏出
- 既存Ruleとの矛盾

---

## 18. 禁止事項

- DomainからInfrastructureへの依存
- DomainからApplicationへの依存
- ApplicationからInfrastructure具体実装への依存
- Feature間直接依存
- SeedworkからFeatureへの依存
- Shared KernelからFeatureへの依存
- Presentationへの業務ルール実装
- Infrastructureへの業務ルール実装

業務上の意味を持つ判断はDomainへ配置する。

---

## 19. Architectureレビューのチェックリスト

### Layer
- Domain / Application / Infrastructure / Presentationの責務が明確
- 各処理が適切なLayer
- Layer間依存方向が正しい

### Module
- Seedworkに業務固有コードなし
- Shared Kernelに不要な共有コードなし
- Feature境界が明確

### Dependency
- Domain -> Applicationなし
- Domain -> Infrastructureなし
- Application -> Infrastructure具体実装なし
- Feature間直接依存なし
- 外部技術が内側へ漏れない

### Domain
- 業務ルールがDomain
- Entity / VO / Aggregate等の責務が明確

### Application
- ユースケース調整に集中
- Domainルール再実装なし
- Repository / UoW等の抽象を利用

### Infrastructure
- Repository等の具体実装がInfrastructure
- MappingがInfrastructure
- DB / ORM / SDKが内側へ漏れない

### Presentation
- 入出力変換に集中
- 業務ルールなし
- Application経由でユースケース実行

---

## 20. 最終原則

業務知識は Domain に置く。
ユースケースの手順は Application に置く。
技術的な実装は Infrastructure に置く。
外部との入出力は Presentation に置く。
DDDの汎用基盤は Seedwork に置く。
複数Featureで共有する業務概念は Shared Kernel に置く。
Featureは業務機能単位で独立させる。
依存方向を制御し、内側へ技術詳細を漏らさない。

判断に迷った場合は、
「これは業務上の意味なのか、処理の手順なのか、技術的な実装なのか、外部との接続なのか」
を基準として配置を決定する。

既存のRuleと矛盾する場合は、まずArchitecture上の責務境界を確認し、その後に各LayerのRuleを適用する。
