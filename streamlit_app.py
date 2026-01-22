import streamlit as st
import requests
from datetime import date
import time

# ----------------------------
# ページ設定
# ----------------------------
st.set_page_config(
    page_title="今日のWikipediaランダム記事",
    layout="wide"
)

st.title("📚 今日のWikipediaランダム記事")
st.caption("Wikipedia日本語版から、今日出会う5つの記事")

# ----------------------------
# 1日1回制限（簡易）
# ----------------------------
today = str(date.today())

if "last_fetch_date" not in st.session_state:
    st.session_state.last_fetch_date = None

if "articles" not in st.session_state:
    st.session_state.articles = []

can_fetch = st.session_state.last_fetch_date != today

# ----------------------------
# Wikipedia API
# ----------------------------
API_URL = "https://ja.wikipedia.org/api/rest_v1/page/random/summary"
HEADERS = {
    "User-Agent": "KU-WebProgramming-Student/1.0 (learning project)"
}
def fetch_random_articles(n=5):
    articles = []

    try:
        for _ in range(n):
            r = requests.get(API_URL,headers=HEADERS, timeout=10)
            r.raise_for_status()      # HTTPエラー検知
            data = r.json()           # JSONでなければ例外

            articles.append({
                "title": data.get("title"),
                "description": data.get("description", ""),
                "extract": data.get("extract", ""),
                "url": data.get("content_urls", {})
                            .get("desktop", {})
                            .get("page", ""),
                "image": data.get("thumbnail", {})
                            .get("source", None)
            })

    except Exception as e:
        # 途中で失敗したら「全体失敗」とする
        with open("out", "a", encoding="utf-8") as f:
            f.write(f"{time.time()} ERROR: {e}\n")
        return None

    return articles

# ----------------------------
# ボタン
# ----------------------------
if st.button("🔄 今日の記事を取得", disabled=not can_fetch):
    result = fetch_random_articles()

    if result is None:
        st.error("記事の取得に失敗しました。時間をおいて、もう一度お試しください。")
    else:
        st.session_state.articles = result
        st.session_state.last_fetch_date = today
        st.rerun()

# ----------------------------
# 記事表示
# ----------------------------
for article in st.session_state.articles:
    st.markdown("---")
    col_left, col_right = st.columns([3, 1])

    with col_left:
        # 大タイトル
        st.markdown(
            f"## {article['title']}"
        )

        # 小見出しサイズの概要
        if article["description"]:
            st.markdown(
                f"### {article['description']}"
            )

        # 本文要約
        st.write(article["extract"])

        # リンク
        st.markdown(
            f"[Wikipediaで読む]({article['url']})"
        )

    with col_right:
        if article["image"]:
            st.image(article["image"], use_container_width=True)
