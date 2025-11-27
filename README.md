# Life Simulator

子供が将来なりたい職業を具体的にイメージするためのシミュレータ

## 📋 プロジェクト概要

子供たちが「将来の夢」を考える際に、世界にどんな職業があり、どのような仕事内容で、どんな学校を出れば目指せるのかなど、十分な情報が提供されていないという課題を解決するプロジェクトです。

このシステムは、世界中のあらゆる職業（違法なものを除く）を包括的に収集し、子供向けに分かりやすく提示することを目指しています。

## 🎯 主な機能

### フェーズ1: データ収集（現在）
- ✅ 国際標準職業分類（ISCO-08）からのデータ収集
- ✅ O*NET（米国労働省）APIからのデータ収集
- ✅ 職業データの重複排除と統合
- ✅ PostgreSQLデータベースへの保存

### フェーズ2: データ拡充（次のステップ）
- 各国の職業統計データの収集
- 給与・従事者数などの統計情報の追加
- 多言語対応（日本語、英語など）
- 教育要件やキャリアパスの情報追加

### フェーズ3: Webシステム開発（今後）
- 子供向けUI/UXの設計
- 職業シミュレーション機能
- インタラクティブな職業探索

## 📁 プロジェクト構造

```
Life-simulator/
├── docs/                          # ドキュメント
│   └── career-data-collection-method.md  # 職業データ収集方法
├── database/                      # データベース関連
│   └── schema.sql                # データベーススキーマ
├── src/                          # ソースコード
│   ├── models/                   # データモデル
│   │   └── occupation.py        # 職業モデル（SQLAlchemy）
│   ├── collectors/               # データ収集
│   │   ├── onet_collector.py    # O*NET APIクライアント
│   │   └── isco_collector.py    # ISCO-08パーサー
│   └── utils/                    # ユーティリティ
│       ├── database.py           # データベース接続管理
│       └── deduplication.py      # 重複排除ロジック
├── config/                       # 設定
│   └── settings.py              # アプリケーション設定
├── tests/                        # テスト
├── data/                         # データファイル（.gitignore）
├── requirements.txt              # Python依存パッケージ
└── .env.example                  # 環境変数のサンプル
```

## 🚀 セットアップ

### 1. 前提条件

- Python 3.9以上
- PostgreSQL 12以上
- Git

### 2. リポジトリのクローン

```bash
git clone https://github.com/koichi1115/Life-simulator.git
cd Life-simulator
```

### 3. 仮想環境の作成と有効化

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 4. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 5. 環境変数の設定

```bash
# .env.exampleをコピーして.envを作成
cp .env.example .env

# .envを編集して必要な情報を設定
# 特に以下の項目を設定してください:
# - DATABASE_URL: PostgreSQL接続情報
# - ONET_USERNAME: O*NET APIユーザー名
# - ONET_PASSWORD: O*NET APIパスワード
```

### 6. データベースのセットアップ

```bash
# PostgreSQLデータベースを作成
createdb life_simulator

# スキーマを適用
psql -d life_simulator -f database/schema.sql
```

## 📊 使い方

### O*NETデータの収集

```python
from src.collectors import OnetCollector

# O*NETクライアントの初期化
collector = OnetCollector()

# 全職業リストを取得
occupations = collector.get_all_occupations()
print(f"取得した職業数: {len(occupations)}")

# 詳細情報付きで収集（最初の10件のみ）
data = collector.collect_comprehensive_data(limit=10, include_details=True)
```

### ISCO-08データの処理

```python
from src.collectors import IscoCollector

# ISCOコレクターの初期化
collector = IscoCollector(data_dir="data/isco")

# サンプルデータの生成（テスト用）
occupations = collector.generate_sample_data()

# CSVからの読み込み（実際のデータがある場合）
# occupations = collector.load_from_csv("data/isco/isco08_structure.csv")

# 大分類でフィルタリング
it_professionals = collector.filter_by_major_group(occupations, "2")
```

### 重複排除

```python
from src.utils import OccupationDeduplicator

# 重複排除の初期化
deduplicator = OccupationDeduplicator(
    similarity_threshold=0.85,
    exact_match_threshold=0.95
)

# 重複排除を実行
deduplicated = deduplicator.deduplicate(occupations)

# レポート生成
report = deduplicator.generate_deduplication_report(occupations)
print(f"重複排除前: {report['total_occupations']}件")
print(f"重複排除後: {report['unique_occupations']}件")
```

### データベース操作

```python
from src.utils import db_manager
from src.models import Occupation

# データベースセッションを使用
with db_manager.get_session() as session:
    # 職業を追加
    occupation = Occupation(
        occupation_name="Software Engineer",
        occupation_code_onet="15-1252.00",
        category_major="Professionals",
        description="ソフトウェアの設計、開発、テストを行う"
    )
    session.add(occupation)
    session.commit()

    # 職業を検索
    all_occupations = session.query(Occupation).all()
    print(f"登録されている職業数: {len(all_occupations)}")
```

## 🧪 テストの実行

```bash
# 全テストを実行
pytest

# カバレッジ付きで実行
pytest --cov=src tests/

# 特定のテストファイルを実行
pytest tests/test_collectors.py
```

## 📖 ドキュメント

詳細なドキュメントは `docs/` ディレクトリにあります：

- [職業データ収集方法](docs/career-data-collection-method.md) - データ収集の包括的な手法

## 🔑 O*NET API キーの取得

O*NET Web Servicesを使用するには、無料のアカウント登録が必要です：

1. https://services.onetcenter.org/ にアクセス
2. "Register" をクリックしてアカウントを作成
3. ユーザー名とパスワードを取得
4. `.env` ファイルに認証情報を設定

## 🗄️ データソース

本プロジェクトは以下のデータソースを使用しています：

- **ISCO-08**: 国際労働機関（ILO）による国際標準職業分類
- **O*NET**: 米国労働省による職業情報ネットワーク
- **各国統計局**: 各国政府による雇用統計データ

## 🤝 コントリビューション

プロジェクトへの貢献を歓迎します！

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📝 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 👥 作成者

- [@koichi1115](https://github.com/koichi1115)

## 🙏 謝辞

- ILO（国際労働機関）- ISCO-08職業分類
- 米国労働省 - O*NET職業情報データベース
- その他のオープンデータ提供者の皆様
