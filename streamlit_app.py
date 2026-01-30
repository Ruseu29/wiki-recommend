import streamlit as st
import requests
from datetime import date
import time
from supabase import create_client
import random

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
tag_choices = {
    # 生き物・自然（脳死で見れる系）
    "哺乳類": "Category:哺乳類",
    "鳥類": "Category:鳥類",
    "恐竜": "Category:恐竜",
    "深海生物": "Category:深海生物",

    # 人物（知的・安定）
    "数学者": "Category:数学者",
    "日本の数学者": "Category:日本の数学者",
    "物理学者": "Category:物理学者",
    "哲学者": "Category:哲学者",
    "計算機科学者": "Category:計算機科学者",

    # 建造物・場所（画像映え）
    "世界遺産": "Category:世界遺産",
    "城": "Category:城",
    "橋": "Category:橋",

    # 雑学・軽め
    "祝日": "Category:祝日",
    "日本の祝日": "Category:日本の祝日",
    "料理": "Category:料理",
    "食材": "Category:食材"
}

# ----------------------------
# 1日1回制限（簡易）
# ----------------------------
today = str(date.today())

# ----------------------------
# カテゴリ別 1日1回制限
# ----------------------------
if "last_fetch_by_category" not in st.session_state:
    # 例: {"哺乳類": "2026-01-30", "数学者": None}
    st.session_state.last_fetch_by_category = {}
if "articles_by_category" not in st.session_state:
    # 例: {"哺乳類": [...], "数学者": [...]}
    st.session_state.articles_by_category = {}
if "can_fetch" not in st.session_state:
    st.session_state.can_fetch = {category:{'date':today,'boolian':True} for category in tag_choices.values()}

for category in tag_choices.values():
    last = st.session_state.can_fetch.get(category)
    st.session_state.can_fetch[category] = (last != today)

# ----------------------------
# Wikipedia API
# ----------------------------
API_URL = "https://ja.wikipedia.org/w/api.php"
SUMMARY_URL = "https://ja.wikipedia.org/api/rest_v1/page/summary/"
HEADERS = {
    "User-Agent": "KU-WebProgramming-Student/1.0 (learning project)"
}

def fetch_random_articles(param,n=5):
    if param == 'random':
        param = random.choice(list(tag_choices.keys()))
    param = dict(tag_choices).get(param,param)
    can_fetch = st.session_state.can_fetch.get(param)
    if not can_fetch:
        print('already exist.')
        return st.session_state.articles_by_category.get(param, [])
    articles = []
    request = {
    "action": "query",            # 情報取得モード
    "list": "categorymembers",    # カテゴリに属するページ一覧
    # "cmnamespace": 0,             # 通常記事のみ
    "cmtitle": param, # 対象カテゴリ（ここを差し替える）
    "cmlimit": 20,                # 取得件数（記事数）
    "format": "json",             # JSONで返す
    }
    try:
        r = requests.get(API_URL, headers=HEADERS ,params=request, timeout=10)
        data = r.json()
        titles = [p["title"] for p in data["query"]["categorymembers"]]
        picked = random.sample(titles, k=min(n, len(titles)))
        print(picked)
        for title in picked:
            r = requests.get(SUMMARY_URL + title, headers=HEADERS, timeout=10)
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
                            .get("source", None),
            })
    except Exception as e:
        with open("out", "a", encoding="utf-8") as f:
            f.write(f"{time.time()} ERROR: {e}\n")
        return None

    print('articles ->',articles)
    return articles,param

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
st.session_state.articles = []
param = st.session_state.get('selected_category',"random")
col1, col2 = st.columns([2, 1])
with col1:
    if st.button("🔄 今日の記事を取得"):
        result,param = fetch_random_articles(param)

        if result is None:
            st.error("記事の取得に失敗しました。")
        else:
            st.session_state.articles_by_category[param] = result
            st.session_state.last_fetch_by_category[param] = today
            st.session_state.selected_category = param  # ★ 追加
            st.rerun()
with col2:
    param = st.selectbox(
        "カテゴリ",
        options=['random'] + list(tag_choices.keys()),
        index=0,
        key="selected_category"
    )

# ----------------------------
# 記事表示
# ----------------------------
if "selected_category" in st.session_state:
    st.write(f"選択カテゴリ: {st.session_state.selected_category[9:]}")
for article in st.session_state.articles_by_category.get(param,[]):
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
            st.image(article["image"], width="stretch")

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
    col_left, col_right = st.columns([4, 1])

    with col_left:
        st.write(row["title"])

    with col_right:
        if st.button("読む", key=f"popular_{row['url']}"):
            send_click_to_db(row["url"], row["title"])
            st.success("📊 クリックを記録しました。Wikipediaへ移動します…")

            st.markdown(
                f"""
                <meta http-equiv="refresh" content="0; url={row['url']}">
                """,
                unsafe_allow_html=True
            )
            st.stop()
