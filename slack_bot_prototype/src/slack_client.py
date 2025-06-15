import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SlackClient:
    """Slack APIとの通信を管理するクライアント"""

    def __init__(self, bot_token: str):
        """
        Args:
            bot_token: Slack Bot User OAuth Token or User OAuth Token
        """
        self.client = WebClient(token=bot_token)
        self.token_type = "Bot" if bot_token.startswith("xoxb-") else "User"
        self._validate_connection()

    def _validate_connection(self):
        """接続確認"""
        try:
            response = self.client.auth_test()
            logger.info(f"Connected as bot: {response['user']} in team: {response['team']}")
        except SlackApiError as e:
            logger.error(f"接続エラー: {e}")
            raise

    def get_channel_messages(self, channel_id: str, hours: int = 24) -> List[Dict]:
        """
        指定チャンネルのメッセージを取得

        Args:
            channel_id: チャンネルID (C1234567890形式)
            hours: 過去何時間分のメッセージを取得するか

        Returns:
            メッセージのリスト
        """
        messages = []
        oldest = (datetime.now() - timedelta(hours=hours)).timestamp()

        try:
            # ページネーション対応
            cursor = None
            while True:
                response = self.client.conversations_history(
                    channel=channel_id, oldest=str(oldest), limit=100, cursor=cursor
                )

                messages.extend(response["messages"])

                if not response.get("has_more", False):
                    break
                cursor = response.get("response_metadata", {}).get("next_cursor")

            logger.info(f"チャンネル {channel_id} から {len(messages)} 件のメッセージを取得")
            return messages

        except SlackApiError as e:
            logger.error(f"メッセージ取得エラー: {e}")
            return []

    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """
        ユーザー情報を取得

        Args:
            user_id: ユーザーID (U1234567890形式)

        Returns:
            ユーザー情報
        """
        try:
            response = self.client.users_info(user=user_id)
            return response["user"]
        except SlackApiError as e:
            logger.error(f"ユーザー情報取得エラー: {e}")
            return None

    def get_reactions(self, channel: str, timestamp: str) -> List[Dict]:
        """
        メッセージのリアクションを取得

        Args:
            channel: チャンネルID
            timestamp: メッセージのタイムスタンプ

        Returns:
            リアクションのリスト
        """
        try:
            response = self.client.reactions_get(channel=channel, timestamp=timestamp)
            message = response.get("message", {})
            return message.get("reactions", [])
        except SlackApiError as e:
            logger.error(f"リアクション取得エラー: {e}")
            return []

    def post_message(self, channel: str, text: str, thread_ts: Optional[str] = None):
        """
        メッセージを投稿

        Args:
            channel: 投稿先チャンネル
            text: メッセージ本文
            thread_ts: スレッドに返信する場合のタイムスタンプ
        """
        try:
            response = self.client.chat_postMessage(channel=channel, text=text, thread_ts=thread_ts)
            logger.info(f"メッセージ投稿成功: {channel}")
            return response
        except SlackApiError as e:
            logger.error(f"メッセージ投稿エラー: {e}")
            raise

    def get_channels(self) -> List[Dict]:
        """
        ボットが参加しているチャンネル一覧を取得

        Returns:
            チャンネル情報のリスト
        """
        channels = []
        try:
            # パブリックチャンネル
            cursor = None
            while True:
                response = self.client.conversations_list(
                    types="public_channel", exclude_archived=True, limit=100, cursor=cursor
                )

                for channel in response["channels"]:
                    if channel.get("is_member", False):
                        channels.append(channel)

                if not response.get("has_more", False):
                    break
                cursor = response.get("response_metadata", {}).get("next_cursor")

            logger.info(f"{len(channels)} 個のチャンネルを取得")
            return channels

        except SlackApiError as e:
            logger.error(f"チャンネル一覧取得エラー: {e}")
            return []

    def enrich_messages_with_user_info(self, messages: List[Dict]) -> List[Dict]:
        """
        メッセージにユーザー情報を追加

        Args:
            messages: メッセージのリスト

        Returns:
            ユーザー情報を含むメッセージのリスト
        """
        user_cache = {}

        for message in messages:
            user_id = message.get("user")
            if user_id and user_id not in user_cache:
                user_info = self.get_user_info(user_id)
                if user_info:
                    user_cache[user_id] = {
                        "real_name": user_info.get("real_name", ""),
                        "display_name": user_info.get("profile", {}).get("display_name", ""),
                        "is_bot": user_info.get("is_bot", False),
                    }

            if user_id in user_cache:
                message["user_info"] = user_cache[user_id]

        return messages
