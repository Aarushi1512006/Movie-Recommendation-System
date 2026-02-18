import streamlit as st
import asyncio
import main  # Direct import of your logic

# Initialize logic on startup
if "data_loaded" not in st.session_state:
    try:
        main.load_pickles()
        st.session_state.data_loaded = True
    except Exception as e:
        st.error(f"Failed to load data files: {e}")

# =============================
# CONFIG
# =============================
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# STYLES (minimal modern)
# =============================
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
<style>
    /* Gen-Z Neon Dark Mode */
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: radial-gradient(circle at 50% 50%, #1a1a2e 0%, #0f0f1b 100%); color: #e0e0e0; }
    .block-container { padding-top: 2rem; max-width: 1400px; }
    .card { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 16px; background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(12px); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
    .card:hover { transform: scale(1.05); box-shadow: 0 0 30px rgba(0, 242, 255, 0.2); border-color: #00f2ff; background: rgba(255, 255, 255, 0.06); }
    .movie-title { font-size: 1rem; font-weight: 600; margin-top: 12px; color: #ffffff; background: linear-gradient(90deg, #00f2ff, #7000ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.2rem; height: 2.4rem; overflow: hidden; }
    .small-muted { color: #a0a0c0; font-size: 0.85rem; background: rgba(0, 242, 255, 0.1); padding: 2px 8px; border-radius: 8px; display: inline-block; margin-bottom: 4px; }
    .stButton>button { border-radius: 12px; background: linear-gradient(45deg, #00f2ff, #7000ff); color: white; border: none; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; transition: all 0.3s; }
    .stButton>button:hover { box-shadow: 0 0 20px rgba(112, 0, 255, 0.6); transform: translateY(-2px); }
    .stTextInput>div>div>input { background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(0, 242, 255, 0.3) !important; border-radius: 15px !important; color: #fff !important; }
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# STATE + ROUTING
# =============================
if "view" not in st.session_state: st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state: st.session_state.selected_tmdb_id = None
if "watchlist" not in st.session_state: st.session_state.watchlist = []

qp_view = st.query_params.get("view")
qp_id = st.query_params.get("id")
if qp_view in ("home", "details"): st.session_state.view = qp_view
if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except: pass

def goto_home():
    st.session_state.view = "home"
    st.query_params["view"] = "home"
    if "id" in st.query_params: del st.query_params["id"]
    st.rerun()

def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.query_params["view"] = "details"
    st.query_params["id"] = str(int(tmdb_id))
    st.rerun()

def goto_watchlist():
    st.session_state.view = "watchlist"
    st.query_params["view"] = "watchlist"
    if "id" in st.query_params: del st.query_params["id"]
    st.rerun()

# =============================
# LOCAL LOGIC BRIDGE (Helper for Async)
# =============================
def api_get_json(path: str, params: dict | None = None):
    params = params or {}
    try:
        def run_async(coro):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)

        if path == "/tmdb/search":
            data = run_async(main.tmdb_search(query=params.get("query"), page=params.get("page", 1)))
            return data, None
        if path == "/home":
            data = run_async(main.home(category=params.get("category", "popular"), limit=params.get("limit", 24)))
            return [m.model_dump() for m in data], None
        if path.startswith("/movie/id/"):
            tmdb_id = int(path.split("/")[-1])
            data = run_async(main.movie_details_route(tmdb_id))
            return data.model_dump(), None
        if path == "/movie/search":
            data = run_async(main.search_bundle(query=params.get("query"), tfidf_top_n=params.get("tfidf_top_n", 12), genre_limit=params.get("genre_limit", 12)))
            return data.model_dump(), None
        if path == "/recommend/genre":
            data = run_async(main.recommend_genre(tmdb_id=params.get("tmdb_id"), limit=params.get("limit", 18)))
            return [m.model_dump() for m in data], None
        return None, f"Local route {path} not mapped."
    except Exception as e:
        return None, f"Local execution failed: {e}"

def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies to show.")
        return
    rows = (len(cards) + cols - 1) // cols
    idx = 0
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards): break
            m = cards[idx]
            idx += 1
            tmdb_id, title, poster = m.get("tmdb_id"), m.get("title", "Untitled"), m.get("poster_url")
            with colset[c]:
                if poster: st.image(poster, width='stretch')
                else: st.write("🖼️ No poster")
                if st.button("Open", key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}"):
                    if tmdb_id: goto_details(tmdb_id)
                st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)

def to_cards_from_tfidf_items(tfidf_items):
    cards = []
    for x in tfidf_items or []:
        tmdb = x.get("tmdb") or {}
        if tmdb.get("tmdb_id"):
            cards.append({"tmdb_id": tmdb["tmdb_id"], "title": tmdb.get("title") or x.get("title") or "Untitled", "poster_url": tmdb.get("poster_url")})
    return cards

def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    keyword_l = keyword.strip().lower()
    if isinstance(data, dict) and "results" in data:
        raw_items = [{"tmdb_id": int(m["id"]), "title": m.get("title") or "", "poster_url": f"{TMDB_IMG}{m.get('poster_path')}" if m.get('poster_path') else None, "release_date": m.get("release_date", "")} for m in data.get("results") or [] if m.get("id") and m.get("title")]
    elif isinstance(data, list):
        raw_items = [{"tmdb_id": int(m.get("tmdb_id") or m.get("id")), "title": m.get("title") or "", "poster_url": m.get("poster_url"), "release_date": m.get("release_date", "")} for m in data if (m.get("tmdb_id") or m.get("id")) and m.get("title")]
    else: return [], []
    matched = [x for x in raw_items if keyword_l in x["title"].lower()]
    final_list = matched if matched else raw_items
    suggestions = [(f"{x['title']} ({x['release_date'][:4]})" if x.get("release_date") else x["title"], x["tmdb_id"]) for x in final_list[:10]]
    cards = [{"tmdb_id": x["tmdb_id"], "title": x["title"], "poster_url": x["poster_url"]} for x in final_list[:limit]]
    return suggestions, cards

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.markdown("## 🎬 Menu")
    if st.button("🏠 Home", width='stretch'): goto_home()
    if st.button("💖 My Obsessions", width='stretch'): goto_watchlist()
    st.markdown("---")
    home_category = st.selectbox("Category", ["trending", "popular", "top_rated", "now_playing", "upcoming"], index=0)
    grid_cols = st.slider("Grid columns", 4, 8, 6)

# =============================
# HEADER
# =============================
st.title("✨ FlixVibe")
st.markdown("<div class='small-muted'>Find your next obsession. No mid recs, just bangers. 🔥</div>", unsafe_allow_html=True)
st.divider()

# =============================
# VIEWS
# =============================
if st.session_state.view == "home":
    typed = st.text_input("🔍 Search the vibe", placeholder="e.g. Batman, Inception, Dune...")
    st.divider()
    if typed.strip():
        if len(typed.strip()) < 2: st.caption("Type at least 2 characters...")
        else:
            data, err = api_get_json("/tmdb/search", params={"query": typed.strip()})
            if err: st.error(f"Search failed: {err}")
            else:
                suggestions, cards = parse_tmdb_search_to_cards(data, typed.strip())
                if suggestions:
                    selected = st.selectbox("Suggestions", ["-- Select --"] + [s[0] for s in suggestions])
                    if selected != "-- Select --": goto_details({s[0]: s[1] for s in suggestions}[selected])
                else: st.info("No results.")
                st.markdown("### Results")
                poster_grid(cards, cols=grid_cols, key_prefix="search_results")
        st.stop()
    st.markdown(f"### 🏠 Home — {home_category.title()}")
    home_cards, err = api_get_json("/home", params={"category": home_category})
    if err: st.error(f"Feed failed: {err}")
    else: poster_grid(home_cards or [], cols=grid_cols, key_prefix="home_feed")

elif st.session_state.view == "details":
    tmdb_id = st.session_state.selected_tmdb_id
    if not tmdb_id:
        st.warning("No movie selected."); st.button("← Back", on_click=goto_home); st.stop()
    st.button("← Back", on_click=goto_home)
    data, err = api_get_json(f"/movie/id/{tmdb_id}")
    if err: st.error(f"Load failed: {err}"); st.stop()
    left, right = st.columns([1, 2.4], gap="large")
    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if data.get("poster_url"): st.image(data["poster_url"], width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"## {data.get('title')}")
        st.markdown(f"<div class='small-muted'>Release: {data.get('release_date', '-')} | Genres: {', '.join([g['name'] for g in data.get('genres', [])])}</div>", unsafe_allow_html=True)
        st.write(data.get("overview") or "No overview.")
        is_in = data["tmdb_id"] in [m["tmdb_id"] for m in st.session_state.watchlist]
        if st.button("💔 Remove" if is_in else "💖 Add to Obsessions"):
            if is_in: st.session_state.watchlist = [m for m in st.session_state.watchlist if m["tmdb_id"] != data["tmdb_id"]]
            else: st.session_state.watchlist.append({"tmdb_id": data["tmdb_id"], "title": data["title"], "poster_url": data.get("poster_url")})
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.divider()
    bundle, err2 = api_get_json("/movie/search", params={"query": data.get("title")})
    if not err2 and bundle:
        st.markdown("#### 🔎 Similar (Local)")
        poster_grid(to_cards_from_tfidf_items(bundle.get("tfidf_recommendations")), cols=grid_cols, key_prefix="tfidf")
        st.markdown("#### 🎭 More Like This (TMDB)")
        poster_grid(bundle.get("genre_recommendations") or [], cols=grid_cols, key_prefix="genre")

elif st.session_state.view == "watchlist":
    st.markdown("### 💖 My Obsessions")
    if not st.session_state.watchlist: st.info("Empty! Go find some bangers."); st.button("Browse", on_click=goto_home)
    else:
        poster_grid(st.session_state.watchlist, cols=grid_cols, key_prefix="watchlist")
        if st.button("Clear All"): st.session_state.watchlist = []; st.rerun()
