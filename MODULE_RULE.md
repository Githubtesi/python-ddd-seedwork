# モジュール生成および配置ルール

## 1. ディレクトリの役割分担
プロジェクト構造は以下の3層で管理し、上位層が下位層のルールを汚さないように制御します。

- **`src/seedwork/` (基盤層)**: 
    - DDDを実装するための抽象クラスや基底クラスのみを配置。
    - 業務ロジックは一切含めない。
- **`src/shared_kernel/` (共有ドメイン層)**: 
    - 複数の機能（スライス）で共有される具体的なドメインモデルを配置。
    - 例：`Address` (住所), `Money` (通貨), `CommonPolicy` (共通計算ルール)。
- **`src/features/` (機能スライス層)**: 
    - 各ビジネス機能単位でフォルダを作成（VSA）。
    - 各スライスは自己完結し、他スライスを直接インポートしない。

## 2. 名簿管理（member_management）の構成例
「名簿管理」を例としたフォルダ構成は以下の通りです。
```plaintext
src/
├── seedwork/              # 基底クラス（Entity等）
├── shared_kernel/         # 共有部品（Email等、他でも使うもの）
└── features/
    └── member_management/  # 「名簿」という垂直スライス
        ├── domain/         # この機能固有の知恵・ルール 
        │   ├── member.py            # Aggregate Root 
        │   └── member_repository.py # Repository 
        ├── use_cases/      # 手順（アプリケーション層） 
        │   ├── register_member.py   # 登録手順
        │   └── deactivate_member.py # 停止手順
        ├── infrastructure/ # 外部接続
        └── presentation/   # 外部との接点（API等）
```

## 3. スライス間連携の禁止事項
- **直接参照の禁止**: `features/todo/` が `features/member/` のモデルを直接 import してはいけません。
- **連携方法**: 
    1. ID（文字列や数値）のみを渡して連携する。
    2. `Domain Event` を発行し、`Subscriber` がそれを受け取って動く。
    3. どうしても型定義が必要なモデルのみ `shared_kernel` へ移動を検討する。