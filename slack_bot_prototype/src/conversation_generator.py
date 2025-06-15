import random
from typing import List, Dict, Tuple
import google.generativeai as genai


class ConversationGenerator:
    """LLMを使用してリアルな会話データを生成するクラス"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        # ユーザーペルソナ
        self.personas = [
            ("田中太郎", "初心者プログラマー、質問が多い"),
            ("佐藤花子", "経験豊富なエンジニア、助けるのが好き"),
            ("山田健一", "プロジェクトマネージャー、進捗を気にする"),
            ("鈴木美咲", "デザイナー、UIUXの観点から意見を出す"),
            ("高橋翔", "新人、熱心だが時々失礼な発言をする"),
            ("伊藤優子", "チームリーダー、ポジティブで励ます"),
            ("渡辺大輔", "バックエンドエンジニア、技術的な話が好き"),
            ("中村愛", "QAエンジニア、細かい点を指摘する"),
        ]
        
        # 会話シナリオテンプレート
        self.scenarios = [
            "新機能の実装について議論",
            "バグ報告とその解決策の相談",
            "締切に関するストレスと励まし",
            "コードレビューでのフィードバック",
            "技術的な質問と回答",
            "プロジェクトの進捗報告",
            "チームビルディングの雑談",
            "新しいツールの導入提案",
            "リリース前の最終確認",
            "トラブルシューティング",
        ]
    
    def generate_conversation_batch(self, num_messages: int = 50) -> List[Dict]:
        """会話のバッチを生成"""
        scenario = random.choice(self.scenarios)
        participants = random.sample(self.personas, k=random.randint(3, 5))
        
        prompt = f"""
        以下の設定でSlackの会話を{num_messages}件生成してください。
        
        シナリオ: {scenario}
        
        参加者:
        {chr(10).join([f"- {name}: {desc}" for name, desc in participants])}
        
        要件:
        1. 自然な会話の流れ
        2. 各メッセージは短め（1-3文程度）
        3. 以下の要素を含める:
           - 通常の業務会話（60%）
           - ポジティブな投稿（感謝、称賛、励まし）（20%）
           - 少しネガティブ/失礼な投稿（10%）
           - 質問や相談（10%）
        4. 絵文字を適度に使用
        5. 時々タイプミスや口語的表現を含める
        
        出力形式（JSON配列）:
        [
            {{"user": "名前", "text": "メッセージ内容", "type": "normal|positive|negative|question"}},
            ...
        ]
        
        JSONのみ出力し、説明は不要です。
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # JSONパース
            import json
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            messages = json.loads(text)
            return messages
            
        except Exception as e:
            print(f"生成エラー: {e}")
            return self._generate_fallback_messages(participants)
    
    def _generate_fallback_messages(self, participants: List[Tuple[str, str]]) -> List[Dict]:
        """フォールバック用の固定メッセージ生成"""
        templates = [
            # 通常の会話
            ("おはようございます！今日も頑張りましょう！", "normal"),
            ("昨日のタスク完了しました", "normal"),
            ("ミーティングは何時からでしたっけ？", "question"),
            ("了解です、確認します", "normal"),
            ("そろそろランチ行きませんか？", "normal"),
            
            # ポジティブ
            ("素晴らしい仕事でした！ありがとうございます！", "positive"),
            ("いつも助けていただいて感謝です🙏", "positive"),
            ("チーム最高！みんなのおかげです！", "positive"),
            ("すごい！よくできましたね！👏", "positive"),
            
            # ネガティブ
            ("なんでこんな簡単なこともできないの？", "negative"),
            ("また遅れるの？困るんだけど", "negative"),
            ("これ全然ダメじゃん", "negative"),
            
            # 質問
            ("このエラーの解決方法わかる人いますか？", "question"),
            ("APIの仕様書ってどこにありますか？", "question"),
            ("デプロイ手順を教えてください", "question"),
        ]
        
        messages = []
        for i in range(20):
            user = random.choice(participants)[0]
            text, msg_type = random.choice(templates)
            messages.append({
                "user": user,
                "text": text,
                "type": msg_type
            })
        
        return messages
    
    def generate_diverse_conversations(self, total_messages: int = 100) -> List[Dict]:
        """多様な会話を生成"""
        all_messages = []
        
        # 複数のシナリオで会話を生成
        while len(all_messages) < total_messages:
            batch = self.generate_conversation_batch(
                num_messages=min(30, total_messages - len(all_messages))
            )
            all_messages.extend(batch)
        
        return all_messages[:total_messages]