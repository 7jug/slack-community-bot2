import logging
from typing import Dict
from datetime import datetime

from src.content_analyzer import ContentAnalyzer
from src.scoring_system import ScoringSystem
from src.slack_client import SlackClient
from src.database import DatabaseManager
from src.notification_system import NotificationSystem, ViolationAlert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageProcessor:
    """Slackメッセージの取得と分析を統合するクラス"""

    def __init__(self, slack_token: str = None, gemini_api_key: str = None, admin_channel_id: str = None):
        self.slack = SlackClient(slack_token) if slack_token else None
        self.analyzer = ContentAnalyzer(gemini_api_key) if gemini_api_key else None
        self.scoring = ScoringSystem()
        self.violations = []
        self.positive_messages = []
        self.db = DatabaseManager()
        self.notification_system = NotificationSystem(slack_token, admin_channel_id) if slack_token else None

    def process_channel(self, channel_id: str, hours: int = 24) -> Dict:
        """
        チャンネルのメッセージを処理

        Args:
            channel_id: 処理対象のチャンネルID
            hours: 過去何時間分を処理するか

        Returns:
            処理結果のサマリー
        """
        logger.info(f"チャンネル {channel_id} の処理を開始")

        # メッセージ取得
        messages = self.slack.get_channel_messages(channel_id, hours)
        if not messages:
            logger.warning("メッセージが取得できませんでした")
            return {}

        # ユーザー情報を追加
        messages = self.slack.enrich_messages_with_user_info(messages)

        # 各メッセージを分析
        for message in messages:
            if self._should_analyze(message):
                self._analyze_message(message, channel_id)

        # スコアリング
        scores = self.scoring.calculate_rankings()

        return {
            "total_messages": len(messages),
            "violations_found": len(self.violations),
            "positive_messages": len(self.positive_messages),
            "top_contributors": scores[:5],
        }

    def _should_analyze(self, message: Dict) -> bool:
        """
        分析対象のメッセージかどうか判定

        Args:
            message: Slackメッセージ

        Returns:
            分析対象の場合True
        """
        # ボットのメッセージは除外
        if message.get("user_info", {}).get("is_bot", False):
            return False

        # サブタイプがあるメッセージ（参加/退出など）は除外
        if message.get("subtype"):
            return False

        # テキストがないメッセージは除外
        if not message.get("text"):
            return False

        return True

    def _analyze_message(self, message: Dict, channel_id: str):
        """
        個別メッセージの分析と記録

        Args:
            message: Slackメッセージ
            channel_id: チャンネルID
        """
        text = message.get("text", "")
        user_id = message.get("user", "")
        user_name = message.get("user_info", {}).get("real_name", user_id)
        timestamp = message.get("ts", "")

        # テキスト分析
        analysis = self.analyzer.analyze_post(text)

        # ガイドライン違反チェック
        if analysis.get("guideline_violation", False):
            violation_data = {
                "user_id": user_id,
                "user_name": user_name,
                "text": text,
                "timestamp": timestamp,
                "channel_id": channel_id,
                "violation_reason": analysis.get("violation_details", ""),
            }
            self.violations.append(violation_data)
            logger.warning(f"ガイドライン違反検出: {user_name}")
            
            # リアルタイム通知送信
            if self.notification_system:
                try:
                    # 違反の重要度を判定
                    violation_text = text.lower()
                    if any(word in violation_text for word in ["緊急", "重大", "深刻", "ひどい"]):
                        severity = "high"
                    elif any(word in violation_text for word in ["不適切", "問題", "良くない"]):
                        severity = "medium" 
                    else:
                        severity = "low"
                    
                    # ViolationAlertを作成
                    from datetime import datetime as dt
                    alert_timestamp = dt.fromtimestamp(float(timestamp)) if isinstance(timestamp, str) else timestamp
                    
                    violation_alert = ViolationAlert(
                        user_id=user_id,
                        user_name=user_name,
                        real_name=message.get("user_info", {}).get("real_name"),
                        message_content=text,
                        violation_reason=analysis.get("violation_details", "ガイドライン違反が検出されました"),
                        channel_id=channel_id,
                        message_id=timestamp,
                        timestamp=alert_timestamp,
                        severity=severity
                    )
                    
                    # アラート送信
                    self.notification_system.send_violation_alert(violation_alert)
                    
                except Exception as e:
                    logger.error(f"違反アラート送信エラー: {e}")

        # ポジティブ投稿チェック
        if analysis.get("is_positive", False):
            self.positive_messages.append(
                {
                    "user_id": user_id,
                    "user_name": user_name,
                    "text": text,
                    "timestamp": timestamp,
                    "channel_id": channel_id,
                    "positive_type": analysis.get("positive_details", ""),
                }
            )
            logger.info(f"ポジティブ投稿検出: {user_name}")

        # リアクション情報取得
        reactions = self.slack.get_reactions(channel_id, timestamp)
        reaction_count = sum(r.get("count", 0) for r in reactions)

        # スコアリングシステムに追加
        self.scoring.add_user_activity(
            user_id=user_id,
            user_name=user_name,
            post_count=1,
            positive_count=1 if analysis.get("is_positive", False) else 0,
            reaction_received=reaction_count,
        )

    def get_violations_report(self) -> str:
        """ガイドライン違反のレポート生成"""
        if not self.violations:
            return "ガイドライン違反は検出されませんでした。"

        report = "【ガイドライン違反レポート】\n\n"
        for v in self.violations:
            report += f"ユーザー: {v['user_name']}\n"
            report += f"投稿内容: {v['text'][:50]}...\n"
            report += f"違反理由: {v['violation_reason']}\n"
            report += f"チャンネル: <#{v['channel_id']}>\n"
            report += "-" * 40 + "\n"

        return report

    def get_positive_report(self) -> str:
        """ポジティブ投稿のレポート生成"""
        if not self.positive_messages:
            return "ポジティブな投稿は検出されませんでした。"

        report = "【ポジティブ投稿レポート】\n\n"
        for p in self.positive_messages[:10]:  # 上位10件
            report += f"ユーザー: {p['user_name']}\n"
            report += f"投稿内容: {p['text'][:50]}...\n"
            report += f"種類: {p['positive_type']}\n"
            report += "-" * 40 + "\n"

        return report

    def notify_violations(self, admin_channel: str):
        """管理者チャンネルに違反を通知"""
        if not self.violations:
            return

        text = "⚠️ ガイドライン違反の可能性がある投稿を検出しました\n\n"
        for v in self.violations:
            text += f"• <@{v['user_id']}> の投稿をチェックしてください\n"

        self.slack.post_message(admin_channel, text)

    def process_message(self, user_id: str, content: str, channel_id: str, message_id: str, timestamp: datetime):
        """
        単一メッセージを分析してデータベースに保存
        
        Args:
            user_id: SlackユーザーID
            content: メッセージ内容
            channel_id: チャンネルID
            message_id: メッセージID
            timestamp: 投稿時刻
        """        
        session = self.db.get_session()
        try:
            # ユーザー情報を取得または作成
            user = self.db.get_or_create_user(
                session=session,
                slack_user_id=user_id,
                user_name=user_id,  # テストデータの場合は後で更新
                real_name=None,
                is_bot=False
            )
            
            # メッセージを分析（Geminiが利用可能な場合）
            analysis_result = {}
            if self.analyzer:
                try:
                    analysis_result = self.analyzer.analyze_post(content)
                except Exception as e:
                    logger.warning(f"分析エラー: {e}")
                    # デフォルト値を設定
                    analysis_result = {
                        "positive_feedback": False,
                        "guideline_violation": False,
                        "contribution_score": 0.0
                    }
            else:
                # テストデータ用のランダム分析結果
                import random
                analysis_result = {
                    "positive_feedback": random.random() < 0.3,  # 30%の確率でポジティブ
                    "guideline_violation": random.random() < 0.05,  # 5%の確率で違反
                    "contribution_score": random.uniform(0, 10),
                    "positive_type": "感謝・賞賛" if random.random() < 0.3 else "",
                    "violation_reason": "不適切な言葉遣い" if random.random() < 0.05 else ""
                }
            
            # メッセージをデータベースに保存
            message_record = self.db.save_message(
                session=session,
                slack_message_id=message_id,
                user=user,
                channel_id=channel_id,
                content=content,
                posted_at=timestamp,
                analysis_result=analysis_result
            )
            
            # 日次スコアを更新
            self.db.update_daily_score(
                session=session,
                user=user,
                date=timestamp,
                post_count=1,
                positive_count=1 if analysis_result.get("positive_feedback", False) else 0,
                violation_count=1 if analysis_result.get("guideline_violation", False) else 0,
                reaction_received=0
            )
            
            return message_record
            
        finally:
            session.close()
