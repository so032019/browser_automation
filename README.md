# X自動化ツール

X（旧Twitter）でのリポスト・フォロー・いいね操作を自動化するPythonツールです。

## 🚀 機能

- **自動検索**: 指定したキーワードでポストを検索
- **自動操作**: リポスト、フォロー、いいねを自動実行
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

## 📊 ログ

実行ログは以下の場所に保存されます：

- `auto_repost/logs/` - 実行ログとエラーログ
- `auto_repost/custom_logs/` - カスタムログ（設定による）

## 🔒 セキュリティ

- `.env`ファイルには機密情報が含まれるため、Gitにコミットされません
- ログファイルも自動的にGitから除外されます
- ブラウザのセッションデータは一時的に保存され、実行後にクリーンアップされます

## 🚨 注意事項

- このツールは教育・研究目的で作成されています
- Xの利用規約を遵守してご使用ください
- 過度な自動化はアカウント制限の原因となる可能性があります
- 適切な間隔を設けて実行することを推奨します

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
