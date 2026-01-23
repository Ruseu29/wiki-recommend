import streamlit as st
import requests
from datetime import date
import time
from supabase import create_client

# ----------------------------
# Supabase 設定
# ----------------------------
SUPABASE_URL = "https://rglluudszoxeuxciupbx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJnbGx1dWRzem94ZXV4Y2l1cGJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkxMzYzMTIsImV4cCI6MjA4NDcxMjMxMn0.ym3Aq9n8YMhRsFIRcsDKmyZCIz9fPNLdwqcKGUp_uhY"
SUPABASE_TABLE = "save_time_key_value"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------------
# ページ設定
# ----------------------------
st.set_page_config(
    page_title="今日のWikipediaランダム記事",
    layout="wide"
)

st.title("📚 今日のWikipediaランダム記事")
st.caption("Wikipedia日本語版から、今日出会う記事")

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
            r = requests.get(API_URL, headers=HEADERS, timeout=10)
            r.raise_for_status()
            data = r.json()

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
        with open("out", "a", encoding="utf-8") as f:
            f.write(f"{time.time()} ERROR: {e}\n")
        return None

    return articles

# ----------------------------
# DB にクリックを記録
# ----------------------------
def send_click_to_db(url, title):
    # 1) 今の click を取得
    res = (
        supabase
        .table(SUPABASE_TABLE)
        .select("click")
        .eq("url", url)
        .execute()
    )

    if res.data:
        new_click = res.data[0]["click"] + 1
    else:
        new_click = 1

    # 2) upsert で保存
    supabase.table(SUPABASE_TABLE).upsert({
        "url": url,
        "title": title,
        "click": new_click
    }).execute()


# ----------------------------
# 記事取得ボタン
# ----------------------------
if st.button("🔄 今日の記事を取得", disabled=not can_fetch):
    result = fetch_random_articles()

    if result is None:
        st.error("記事の取得に失敗しました。")
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
        st.markdown(f"## {article['title']}")

        if article["description"]:
            st.markdown(f"### {article['description']}")

        st.write(article["extract"])

        if st.button("Wikipediaで読む", key=f"read_{article['url']}"):
            send_click_to_db(article["url"], article["title"])
            st.success("📊 クリックを記録しました。Wikipediaへ移動します…")

            st.markdown(
                f"""
                <meta http-equiv="refresh" content="0; url={article['url']}">
                """,
                unsafe_allow_html=True
            )
            st.stop()

    with col_right:
        if article["image"]:
            st.image(article["image"], use_container_width=True)

# ----------------------------
# 人気記事 上位3件
# ----------------------------
st.markdown("---")
st.subheader("🔥 人気の記事")

top = (
    supabase
    .table(SUPABASE_TABLE)
    .select("title,url,click,last_clicked_at")
    .order("click", desc=True)
    .limit(3)
    .execute()
)

for row in top.data:
    st.write(f"- {row['title']}")

