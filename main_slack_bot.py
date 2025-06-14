#!/usr/bin/env python3
"""
Slackボットのメインスクリプト
定期実行またはコマンドラインから実行可能
"""

import argparse
import os
import sys
import time

import schedule

# src ディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import logging

from message_processor import MessageProcessor
from config_manager import SecureConfigManager
from security_utils import SecureLogger

# セキュアロガーの設定
secure_logger = SecureLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# セキュアな設定管理
config_manager = SecureConfigManager("config")
config = config_manager.load_config()


def run_analysis(channel_id: str = None, admin_channel: str = None):
    """
    分析を実行

    Args:
        channel_id: 特定チャンネルのみ分析する場合のID
        admin_channel: 管理者通知用チャンネルID
    """
    slack_token = config.get("SLACK_BOT_TOKEN")
    gemini_key = config.get("GEMINI_API_KEY")

    if not slack_token or not gemini_key:
        logger.error("必要な環境変数が設定されていません")
        secure_logger.log_security_event("CONFIG_ERROR", "Missing required API keys")
        return

    try:
        processor = MessageProcessor(slack_token, gemini_key)

        if channel_id:
            # 特定チャンネルのみ
            logger.info(f"チャンネル {channel_id} の分析を開始")
            result = processor.process_channel(channel_id)
            print_summary(result, channel_id)
        else:
            # 全チャンネル
            logger.info("全チャンネルの分析を開始")
            slack_client = processor.slack
            channels = slack_client.get_channels()

            for channel in channels:
                ch_id = channel["id"]
                ch_name = channel["name"]
                logger.info(f"チャンネル #{ch_name} を分析中...")
                result = processor.process_channel(ch_id)
                print_summary(result, ch_name)

        # レポート出力
        print("\n" + "=" * 50)
        print(processor.get_violations_report())
        print("\n" + "=" * 50)
        print(processor.get_positive_report())
        print("\n" + "=" * 50)
        print("【貢献度ランキング】")
        scores = processor.scoring.calculate_rankings()
        for i, score in enumerate(scores[:10], 1):
            print(f"{i}. {score.user_name}: {score.total_score}点")

        # 管理者チャンネルへの通知
        if admin_channel and processor.violations:
            processor.notify_violations(admin_channel)
            logger.info(f"管理者チャンネル {admin_channel} に通知を送信")

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        raise


def print_summary(result: dict, channel_name: str):
    """分析結果のサマリーを表示"""
    if not result:
        return

    print(f"\n[{channel_name}] 分析結果:")
    print(f"  総メッセージ数: {result.get('total_messages', 0)}")
    print(f"  ガイドライン違反: {result.get('violations_found', 0)}")
    print(f"  ポジティブ投稿: {result.get('positive_messages', 0)}")

    if result.get("top_contributors"):
        print("  上位貢献者:")
        for contributor in result["top_contributors"][:3]:
            print(f"    - {contributor.user_name}: {contributor.total_score}点")


def scheduled_job():
    """スケジュール実行用のジョブ"""
    logger.info("定期実行を開始します")
    admin_channel = config.get("ADMIN_CHANNEL_ID", "")
    run_analysis(admin_channel=admin_channel)


def main():
    parser = argparse.ArgumentParser(description="Slack分析ボット")
    parser.add_argument("--channel", help="特定チャンネルのみ分析（チャンネルID）")
    parser.add_argument("--admin-channel", help="管理者通知チャンネルID")
    parser.add_argument("--schedule", action="store_true", help="定期実行モード（1日1回）")
    parser.add_argument("--test", action="store_true", help="テスト実行（最初のチャンネルのみ）")

    args = parser.parse_args()

    if args.schedule:
        # 定期実行モード
        logger.info("定期実行モードで起動しました")
        # 毎日午前9時に実行
        schedule.every().day.at("09:00").do(scheduled_job)

        # 初回は即実行
        scheduled_job()

        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにチェック
    elif args.test:
        # テストモード
        logger.info("テストモードで実行")
        slack_token = config.get("SLACK_BOT_TOKEN")
        gemini_key = config.get("GEMINI_API_KEY")

        if not slack_token or not gemini_key:
            logger.error("必要な環境変数が設定されていません")
            secure_logger.log_security_event("CONFIG_ERROR", "Missing required API keys in test mode")
            return

        processor = MessageProcessor(slack_token, gemini_key)
        channels = processor.slack.get_channels()

        if channels:
            first_channel = channels[0]
            logger.info(f"テスト実行: #{first_channel['name']}")
            result = processor.process_channel(first_channel["id"], hours=24 * 7)  # 1週間分
            print_summary(result, first_channel["name"])
        else:
            logger.error("参加しているチャンネルが見つかりません")
    else:
        # 単発実行
        run_analysis(args.channel, args.admin_channel)


if __name__ == "__main__":
    main()
