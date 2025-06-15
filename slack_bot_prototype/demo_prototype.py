import os
import random

from dotenv import load_dotenv

from src.content_analyzer import ContentAnalyzer
from src.scoring_system import ScoringSystem

# .envファイルから環境変数を読み込む
load_dotenv("config/.env")


def generate_demo_data():
    """デモ用のSlack投稿データを生成"""
    users = [
        ("U001", "田中太郎"),
        ("U002", "山田花子"),
        ("U003", "佐藤次郎"),
        ("U004", "鈴木美香"),
        ("U005", "高橋健一"),
    ]

    posts = [
        # ポジティブな投稿
        "みんなのおかげで理解できました！本当にありがとうございます！",
        "素晴らしい解説でした。とても参考になります。",
        "困っている人がいたら、遠慮なく質問してください。一緒に解決しましょう！",
        "今日学んだことをまとめてシェアします。お役に立てれば幸いです。",
        "チームメンバーの協力に感謝します！最高のチームです！",
        # 通常の投稿
        "課題3について質問があります。",
        "明日のミーティングは何時からですか？",
        "資料をアップロードしました。",
        # ネガティブな投稿（ガイドライン違反の可能性）
        "こんな簡単なこともわからないの？",
        "その考え方は完全に間違ってますね。",
    ]

    demo_data = []
    for _ in range(20):
        user_id, user_name = random.choice(users)
        post = random.choice(posts)
        reactions_count = random.randint(0, 10)

        demo_data.append(
            {
                "user_id": user_id,
                "user_name": user_name,
                "text": post,
                "reactions_count": reactions_count,
            }
        )

    return demo_data


def run_demo():
    """プロトタイプのデモ実行"""

    # APIキーの確認
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your-gemini-api-key-here":
        print("❌ GEMINI_API_KEYが設定されていません。")
        print("\n=== セットアップ手順 ===")
        print("1. config/.env.exampleをconfig/.envにコピー")
        print("2. Gemini APIキーを取得（https://makersuite.google.com/app/apikey）")
        print("3. .envファイルのGEMINI_API_KEYに設定")
        return

    print("=== Slackボット プロトタイプ デモ ===\n")

    # システムの初期化
    analyzer = ContentAnalyzer(api_key)
    scoring = ScoringSystem()

    # デモデータの生成
    demo_posts = generate_demo_data()

    print(f"📊 {len(demo_posts)}件の投稿を分析します...\n")

    violations = []
    positive_feedbacks = []

    # 各投稿を分析
    for i, post_data in enumerate(demo_posts, 1):
        print(f"分析中 [{i}/{len(demo_posts)}]: {post_data['user_name']}")

        # 投稿を分析
        result = analyzer.analyze_post(post_data["text"])

        # スコアを更新
        scoring.update_user_post(
            post_data["user_id"], post_data["user_name"], result, post_data["reactions_count"]
        )

        # 違反やポジティブ投稿を記録
        if result.get("guideline_violation", 0) > 50:
            violations.append(
                {
                    "user": post_data["user_name"],
                    "text": post_data["text"][:50] + "...",
                    "reason": result.get("violation_reason", "不明"),
                }
            )

        if result.get("positive_feedback", False):
            positive_feedbacks.append(
                {
                    "user": post_data["user_name"],
                    "text": post_data["text"][:50] + "...",
                    "type": result.get("positive_type", "不明"),
                }
            )

    # 結果の表示
    print("\n" + "=" * 50)
    print("📋 分析結果サマリー")
    print("=" * 50)

    # ガイドライン違反の可能性
    if violations:
        print(f"\n⚠️  ガイドライン違反の可能性がある投稿: {len(violations)}件")
        for v in violations[:3]:  # 最初の3件のみ表示
            print(f"  - {v['user']}: {v['text']}")
            print(f"    理由: {v['reason']}")

    # ポジティブフィードバック
    if positive_feedbacks:
        print(f"\n👍 ポジティブフィードバック: {len(positive_feedbacks)}件")
        for p in positive_feedbacks[:3]:  # 最初の3件のみ表示
            print(f"  - {p['user']}: {p['text']}")
            print(f"    種類: {p['type']}")

    # ランキング表示
    print("\n🏆 貢献度ランキング TOP 5")
    print("-" * 50)
    rankings = scoring.get_rankings(top_n=5)

    for r in rankings:
        print(f"{r['rank']}位: {r['user_name']}")
        print(f"   総合スコア: {r['total_score']:.1f}")
        print(
            f"   投稿数: {r['total_posts']}, ポジティブ: {r['positive_posts']}, "
            f"リアクション: {r['reactions_received']}"
        )
        print()

    # スコアデータを保存
    scoring.save_to_file("data/scores.json")
    print("✅ スコアデータを data/scores.json に保存しました")


if __name__ == "__main__":
    run_demo()
