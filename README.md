# Slack コミュニティ分析ボット

Slackのメッセージを分析し、ガイドライン違反検出とユーザー貢献度スコアリングを行うボットです。

## 主な機能

- **メッセージ分析**: Google Gemini AIを使用してSlackメッセージを分析
- **違反検出**: 不適切な投稿を自動検出
- **ポジティブ認識**: 感謝や称賛などの前向きな投稿を識別
- **スコアリング**: ユーザーの貢献度を数値化

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 設定ファイルの作成

```bash
cp config/.env.template config/.env
```

`config/.env`を編集し、以下を設定：
```
SLACK_BOT_TOKEN=xoxp-your-slack-bot-token
GEMINI_API_KEY=your-gemini-api-key
```

### 3. 実行

**デモ実行（Slack接続不要）:**
```bash
python demo_prototype.py
```

**Slack連携実行:**
```bash
python main_slack_bot.py --test
```

## ファイル構成

```
src/
├── slack_client.py         # Slack API接続
├── content_analyzer.py     # Gemini AI分析
├── scoring_system.py       # スコアリングシステム
└── message_processor.py    # メイン処理ロジック

main_slack_bot.py          # エントリーポイント
demo_prototype.py          # デモ実行
```
