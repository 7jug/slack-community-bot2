# Slack コミュニティ管理ボット

Slackワークスペース内のコミュニティ活動を自動分析し、ガイドライン違反の検出、ポジティブな貢献の認識、メンバーのエンゲージメントスコアを管理するボットです。

## 主な機能

- **コンテンツ分析**: Google Gemini AIを使用してメッセージを自動分析
- **違反検出**: 不適切なコンテンツを識別し、管理者に通知
- **ポジティブ認識**: 感謝、称賛、有益な貢献を認識
- **スコアリングシステム**: ユーザーのエンゲージメントと貢献度を追跡
- **表彰システム**: 日次・週次・月次のMVP認定
- **Web管理画面**: 監視と管理のための管理者インターフェース
- **リアルタイム通知**: ポリシー違反の即座アラート

## クイックスタート

### 前提条件

- Python 3.8以上
- 管理者権限を持つSlackワークスペース
- Google AI APIへのアクセス

### インストール

1. リポジトリをクローン:
```bash
git clone https://github.com/your-username/slack-community-bot.git
cd slack-community-bot
```

2. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

3. ボットを設定:
```bash
python setup_secure_config.py
```

4. Slack Appのセットアップ（`docs/slack_app_setup.md`を参照）

### 基本的な使用方法

**ボットをテスト:**
```bash
python main_slack_bot.py --test
```

**Web管理画面を起動:**
```bash
python web_app.py
```

**日次分析をスケジュール:**
```bash
python main_slack_bot.py --schedule
```

## 設定

ボットはセキュアな設定システムを使用します。セットアップウィザードを実行して開始してください:

```bash
python setup_secure_config.py
```

必要な設定項目:
- Slack Bot Token（`xoxp-`で始まるOAuthトークン）
- Google Gemini APIキー
- 通知用管理者チャンネルID

## アーキテクチャ

```
src/
├── slack_client.py         # Slack API連携
├── content_analyzer.py     # Gemini AIによるメッセージ分析
├── scoring_system.py       # ユーザー貢献度スコアリング
├── database.py            # データ永続化層
├── notification_system.py # リアルタイムアラートと表彰
└── security_utils.py      # セキュリティとログユーティリティ
```

## Web管理画面

以下を実行してWebインターフェースにアクセス:

```bash
python web_app.py
```

`http://localhost:5000`でアクセス可能

機能:
- ユーザーアクティビティ概要
- メッセージ履歴と分析結果
- 違反レポート
- 貢献度ランキング

## セキュリティ

このプロジェクトは包括的なセキュリティ対策を実装しています:

- 暗号化された設定ストレージ
- セキュアロギング（センシティブデータを自動除去）
- 全設定項目の入力検証
- ファイル権限管理

詳細は`SECURITY.md`を参照してください。

## API使用量とコスト

**Gemini AI（無料枠）:**
- 1分間に15リクエスト
- 推定コスト: 1日500メッセージで月額約$1-2

**レート制限:**
- API呼び出し間の4.5秒遅延を内蔵
- 失敗したリクエストの自動再試行ロジック

## 開発に参加する

1. リポジトリをフォーク
2. 機能ブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更をコミット（`git commit -m 'Add some amazing feature'`）
4. ブランチにプッシュ（`git push origin feature/amazing-feature`）
5. プルリクエストを開く

### 開発環境のセットアップ

```bash
# 開発用依存関係をインストール
pip install -r requirements.txt

# テスト実行
python -m pytest tests/

# コードフォーマット
ruff format .

# 型チェック
mypy src/
```

## デプロイメント

本番環境でのデプロイ:

1. 適切な環境変数を設定
2. 本番データベース（PostgreSQL推奨）を使用
3. リバースプロキシ（nginx）を設定
4. SSL証明書を設定
5. 監視とログ記録を有効化

## トラブルシューティング

**よくある問題:**

1. **ボットが応答しない**: Slackトークンの権限を確認
2. **Gemini APIエラー**: APIキーとレート制限を確認
3. **データベースエラー**: dataディレクトリの書き込み権限を確認

**ヘルプの入手:**

- 詳細なガイドは`docs/`ディレクトリを確認
- `logs/`ディレクトリのログを確認
- 設定検証を実行: `echo "2" | python setup_secure_config.py`

## ライセンス

このプロジェクトはMITライセンスの下で公開されています - 詳細はLICENSEファイルを参照してください。

## 謝辞

- Google Gemini AI（コンテンツ分析）
- Slack API（プラットフォーム連携）
- Flask（Webインターフェース）
- SQLAlchemy（データ管理）

---

**注意**: このボットはコミュニティ管理を目的としており、組織のポリシーに従って適切な権限と責任ある使用が必要です。