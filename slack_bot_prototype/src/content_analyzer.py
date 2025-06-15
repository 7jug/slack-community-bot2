import json
import time
from typing import Dict, List

import google.generativeai as genai


class ContentAnalyzer:
    """Geminiを使用した投稿内容分析クラス"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.last_request_time = 0
        self.request_interval = 4.5  # 無料枠: 15リクエスト/分 = 4秒に1回

    def analyze_post(self, text: str) -> Dict:
        """投稿を分析し、ガイドライン違反やポジティブ度を判定"""
        
        # レート制限対策
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_interval:
            time.sleep(self.request_interval - time_since_last_request)
        
        self.last_request_time = time.time()

        prompt = f"""
        以下のSlack投稿を分析し、JSON形式で結果を返してください：
        
        投稿内容: "{text}"
        
        分析項目:
        1. guideline_violation: ガイドライン違反の可能性（0-100%）
        2. violation_reason: 違反理由（違反の場合のみ）
        3. positive_feedback: ポジティブフィードバックかどうか（true/false）
        4. positive_type: ポジティブの種類（感謝、称賛、励まし、その他）
        5. contribution_score: 貢献度スコア（0-10）
        
        返答はJSON形式のみで、説明は不要です。
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # JSONを抽出（Geminiの応答からJSONブロックを取り出す）
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            return json.loads(result_text)

        except Exception as e:
            print(f"分析エラー: {e}")
            return {
                "guideline_violation": 0,
                "violation_reason": None,
                "positive_feedback": False,
                "positive_type": None,
                "contribution_score": 0,
            }

    def batch_analyze(self, posts: List[str]) -> List[Dict]:
        """複数の投稿をバッチ処理"""
        results = []
        for post in posts:
            result = self.analyze_post(post)
            results.append(result)
        return results
