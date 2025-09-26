# X自動化ツール

X（旧Twitter）でのリポスト・フォロー・いいね操作を自動化するPythonツールです。

## 🚀 機能

- **自動検索**: 指定したキーワードでポストを検索
- **自動操作**: リポスト、フォロー、いいねを自動実行
- **BAN対策**: 人間らしい行動パターンでアカウント制限を回避
- **ログイン管理**: セッション管理とCookie保存
- **Slack通知**: 実行結果をSlackに通知
- **ログ出力**: 詳細な実行ログを記録

## 📋 必要な環境

- Python 3.8以上
- Google Chrome または Brave Browser
- X（旧Twitter）アカウント

## 🛠️ セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd x-automation-tool
```

### 2. 仮想環境の作成

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate     # Windows
```

### 3. 依存関係のインストール

```bash
cd auto_repost
pip install -r requirements.txt
```

### 4. 設定ファイルの作成

```bash
cp .env.example .env
```

`.env`ファイルを編集して、実際の設定値を入力してください：

```env
X_USERNAME=your_x_username
X_PASSWORD=your_x_password
SLACK_API_URL=your_slack_api_url
SLACK_API_KEY=your_slack_api_key
```

## 🎯 使用方法

### 基本的な実行

```bash
cd auto_repost
./run_automation.sh
```

### オプション付き実行

```bash
# ヘッドレスモードで実行
./run_automation.sh --headless

# 最大ポスト数を指定
./run_automation.sh --max-posts 10

# ブラウザを表示して実行
./run_automation.sh --visible

# デバッグモードで実行
./run_automation.sh --debug
```

### Pythonスクリプト直接実行

```bash
python main.py
```

## 📁 プロジェクト構造

```
.
├── .env.example              # 設定ファイルのサンプル
├── .gitignore               # Git除外設定
├── README.md                # このファイル
├── auto_repost/             # メインプロジェクト
│   ├── main.py              # エントリーポイント
│   ├── requirements.txt     # Python依存関係
│   ├── run_automation.sh    # 実行スクリプト
│   ├── config/              # 設定ファイル
│   ├── docs/                # ドキュメント
│   ├── src/                 # ソースコード
│   │   ├── automation/      # 自動化処理
│   │   └── utils/           # ユーティリティ
│   └── tests/               # テストファイル
└── venv/                    # 仮想環境（Git除外）
```

## ⚙️ 設定項目

### 基本設定

| 項目 | 説明 | デフォルト値 |
|------|------|-------------|
| `X_USERNAME` | Xのユーザー名 | - |
| `X_PASSWORD` | Xのパスワード | - |
| `MAX_POSTS_PER_SESSION` | 1回の実行で処理する最大ポスト数 | 5 |
| `DELAY_MIN` | 操作間の最小待機時間（秒） | 3 |
| `DELAY_MAX` | 操作間の最大待機時間（秒） | 7 |
| `HEADLESS` | ヘッドレスモードの有効/無効 | false |
| `STEALTH_MODE` | ステルスモードの有効/無効 | true |
| `BROWSER_PATH` | ブラウザの実行パス | - |

### BAN対策設定

| 項目 | 説明 | デフォルト値 |
|------|------|-------------|
| `ENABLE_BAN_PREVENTION` | BAN対策機能の有効/無効 | true |
| `ENABLE_HOME_BROWSING` | ホーム経由ナビゲーションの有効/無効 | true |
| `POST_READING_MIN` | ポスト読み込み時間の最小値（秒） | 2.0 |
| `POST_READING_MAX` | ポスト読み込み時間の最大値（秒） | 5.0 |
| `PRE_ACTION_WAIT_MIN` | アクション前待機時間の最小値（秒） | 1.0 |
| `PRE_ACTION_WAIT_MAX` | アクション前待機時間の最大値（秒） | 3.0 |
| `DELAY_VARIATION_FACTOR` | 遅延時間の変動係数（0.0-1.0） | 0.5 |

## 📊 ログ

実行ログは以下の場所に保存されます：

- `auto_repost/logs/` - 実行ログとエラーログ
- `auto_repost/custom_logs/` - カスタムログ（設定による）

## 🔒 セキュリティ

- `.env`ファイルには機密情報が含まれるため、Gitにコミットされません
- ログファイルも自動的にGitから除外されます
- ブラウザのセッションデータは一時的に保存され、実行後にクリーンアップされます

## 🛡️ BAN対策機能

このツールには、アカウント制限を回避するための高度なBAN対策機能が搭載されています：

### 主な機能

- **人間らしい行動パターン**: ポスト閲覧、返信確認、自然な待機時間
- **ホーム経由ナビゲーション**: 2回目以降のポストはホームタイムライン経由でアクセス
- **ランダム遅延**: 動的に調整される遅延時間で一定パターンを回避
- **ダミー行動**: 実際のユーザー行動を模倣した自然な操作

### パフォーマンス影響

- **追加時間**: 1ポストあたり約5-12秒の追加時間
- **全体への影響**: 10ポスト処理で約1-2分の増加
- **効率性**: BAN回避効果を考慮すると許容範囲内

### 設定モード

```env
# 高速モード（BAN対策軽微）
POST_READING_MIN=1.0
POST_READING_MAX=2.0
PRE_ACTION_WAIT_MIN=0.5
PRE_ACTION_WAIT_MAX=1.0

# 安全モード（BAN対策強化）
POST_READING_MIN=3.0
POST_READING_MAX=7.0
PRE_ACTION_WAIT_MIN=2.0
PRE_ACTION_WAIT_MAX=4.0
```

## 🚨 注意事項

- このツールは教育・研究目的で作成されています
- Xの利用規約を遵守してご使用ください
- 過度な自動化はアカウント制限の原因となる可能性があります
- BAN対策機能を有効にして適切な間隔で実行することを推奨します

## 🐛 トラブルシューティング

### よくある問題

1. **ブラウザが起動しない**
   - `BROWSER_PATH`の設定を確認してください
   - ブラウザがインストールされているか確認してください

2. **ログインに失敗する**
   - ユーザー名とパスワードが正しいか確認してください
   - 2要素認証が有効な場合は、アプリパスワードを使用してください

3. **要素が見つからない**
   - Xのページ構造が変更された可能性があります
   - `config/selectors.json`の更新が必要な場合があります

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

バグ報告や機能要望は、GitHubのIssuesでお知らせください。
