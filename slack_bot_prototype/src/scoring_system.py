import json
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class UserScore:
    """ユーザーのスコア情報"""

    user_id: str
    user_name: str
    post_count: int = 0
    positive_count: int = 0
    reaction_count: int = 0
    violation_count: int = 0
    total_score: float = 0.0

    def calculate_total_score(self) -> float:
        """総合スコアを計算"""
        return (
            self.post_count * 1.0
            + self.positive_count * 5.0
            + self.reaction_count * 2.0
            - self.violation_count * 10.0
        )


class ScoringSystem:
    """貢献度スコアリングシステム"""

    def __init__(self):
        self.users: Dict[str, UserScore] = {}

    def add_user_activity(
        self,
        user_id: str,
        user_name: str,
        post_count: int = 0,
        positive_count: int = 0,
        reaction_received: int = 0,
        violation_count: int = 0,
    ):
        """ユーザーのアクティビティを追加"""
        if user_id not in self.users:
            self.users[user_id] = UserScore(user_id=user_id, user_name=user_name)

        user = self.users[user_id]
        user.post_count += post_count
        user.positive_count += positive_count
        user.reaction_count += reaction_received
        user.violation_count += violation_count

    def update_user_post(
        self, user_id: str, user_name: str, analysis_result: Dict, reactions_count: int = 0
    ):
        """ユーザーの投稿に基づいてスコアを更新（後方互換性のため残す）"""
        positive_count = 1 if analysis_result.get("positive_feedback", False) else 0
        violation_count = 1 if analysis_result.get("guideline_violation", False) else 0

        self.add_user_activity(
            user_id=user_id,
            user_name=user_name,
            post_count=1,
            positive_count=positive_count,
            reaction_received=reactions_count,
            violation_count=violation_count,
        )

    def calculate_rankings(self) -> List[UserScore]:
        """ランキングを計算"""
        sorted_users = sorted(
            self.users.values(), key=lambda u: u.calculate_total_score(), reverse=True
        )
        return sorted_users

    def get_rankings(self, top_n: int = 10) -> List[Dict]:
        """ランキングを取得（辞書形式）"""
        sorted_users = self.calculate_rankings()

        rankings = []
        for rank, user in enumerate(sorted_users[:top_n], 1):
            rankings.append(
                {
                    "rank": rank,
                    "user_id": user.user_id,
                    "user_name": user.user_name,
                    "total_score": user.calculate_total_score(),
                    "post_count": user.post_count,
                    "positive_count": user.positive_count,
                    "reaction_count": user.reaction_count,
                }
            )

        return rankings

    def save_to_file(self, filepath: str):
        """スコアデータをファイルに保存"""
        data = {
            user_id: {
                "user_name": score.user_name,
                "post_count": score.post_count,
                "positive_count": score.positive_count,
                "reaction_count": score.reaction_count,
                "violation_count": score.violation_count,
                "total_score": score.total_score,
            }
            for user_id, score in self.users.items()
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath: str):
        """ファイルからスコアデータを読み込み"""
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            self.users = {}
            for user_id, score_data in data.items():
                self.users[user_id] = UserScore(
                    user_id=user_id,
                    user_name=score_data["user_name"],
                    post_count=score_data.get("post_count", 0),
                    positive_count=score_data.get("positive_count", 0),
                    reaction_count=score_data.get("reaction_count", 0),
                    violation_count=score_data.get("violation_count", 0),
                    total_score=score_data.get("total_score", 0.0),
                )
        except FileNotFoundError:
            print(f"スコアファイルが見つかりません: {filepath}")
