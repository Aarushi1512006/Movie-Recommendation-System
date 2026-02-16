import requests
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
# API_BASE is no longer needed but kept as placeholder for helper logic
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
    * {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 50% 50%, #1a1a2e 0%, #0f0f1b 100%);
        color: #e0e0e0;
    }
    
    .block-container { 
        padding-top: 2rem; 
        max-width: 1400px; 
    }
    
    /* Glassmorphism Cards */
    .card { 
        border: 1px solid rgba(255, 255, 255, 0.1); 
        border-radius: 24px; 
        padding: 16px; 
        background: rgba(255, 255, 255, 0.03); 
        backdrop-filter: blur(12px);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .card:hover {
        transform: scale(1.05);
        box-shadow: 0 0 30px rgba(0, 242, 255, 0.2);
        border-color: #00f2ff;
        background: rgba(255, 255, 255, 0.06);
    }
    
    .movie-title { 
        font-size: 1rem; 
        font-weight: 600;
        margin-top: 12px;
        color: #ffffff;
        background: linear-gradient(90deg, #00f2ff, #7000ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.2rem; 
        height: 2.4rem; 
        overflow: hidden; 
    }

    .small-muted { 
        color: #a0a0c0; 
        font-size: 0.85rem;
        background: rgba(0, 242, 255, 0.1);
        padding: 2px 8px;
        border-radius: 8px;
        display: inline-block;
        margin-bottom: 4px;
    }

    /* Buttons & Inputs */
    .stButton>button {
        border-radius: 12px;
        background: linear-gradient(45deg, #00f2ff, #7000ff);
        color: white;
        border: none;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(112, 0, 255, 0.6);
        transform: translateY(-2px);
    }

    /* Search Input styling */
    .stTextInput>div>div>input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(0, 242, 255, 0.3) !important;
        border-radius: 15px !important;
        color: #fff !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# STATE + ROUTING (single-file pages)
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"  # home | details
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []  # list of movie cards

qp_view = st.query_params.get("view")
qp_id = st.query_params.get("id")
if qp_view in ("home", "details"):
    st.session_state.view = qp_view
if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except:
        pass


def goto_home():
    st.session_state.view = "home"
    st.query_params["view"] = "home"
    if "id" in st.query_params:
        del st.query_params["id"]
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
    if "id" in st.query_params:
        del st.query_params["id"]
    st.rerun()


# =============================
# LOCAL LOGIC BRIDGE (Replacement for API)
# =============================
def api_get_json(path: str, params: dict | None = None):
    """
    Instead of calling Render, we call main.py functions directly.
    """
    params = params or {}
    
    try:
        # Helper to run async functions in Streamlit sync thread
        def run_async(coro):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)

        # Map 'paths' to local functions in main.py
        if path == "/tmdb/search":
            data = run_async(main.tmdb_search(query=params.get("query"), page=params.get("page", 1)))
            return data, None
            
        if path == "/home":
            data = run_async(main.home(category=params.get("category", "popular"), limit=params.get("limit", 24)))
            # The FastAPI route returns Pydantic models, we convert to dict for app.py
            return [m.model_dump() for m in data], None
            
        if path.startswith("/movie/id/"):
            tmdb_id = int(path.split("/")[-1])
            data = run_async(main.movie_details_route(tmdb_id))
            return data.model_dump(), None
            
        if path == "/movie/search":
            data = run_async(main.search_bundle(
                query=params.get("query"), 
                tfidf_top_n=params.get("tfidf_top_n", 12),
                genre_limit=params.get("genre_limit", 12)
            ))
            return data.model_dump(), None
            
        if path == "/recommend/genre":
            data = run_async(main.recommend_genre(
                tmdb_id=params.get("tmdb_id"),
                limit=params.get("limit", 18)
            ))
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
            if idx >= len(cards):
                break
            m = cards[idx]
            idx += 1

            tmdb_id = m.get("tmdb_id")
            title = m.get("title", "Untitled")
            poster = m.get("poster_url")

            with colset[c]:
                if poster:
                    st.image(poster, width='stretch')
                else:
                    st.write("🖼️ No poster")

                if st.button("Open", key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}"):
                    if tmdb_id:
                        goto_details(tmdb_id)

                st.markdown(
                    f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True
                )


def to_cards_from_tfidf_items(tfidf_items):
    cards = []
    for x in tfidf_items or []:
        tmdb = x.get("tmdb") or {}
        if tmdb.get("tmdb_id"):
            cards.append(
                {
                    "tmdb_id": tmdb["tmdb_id"],
                    "title": tmdb.get("title") or x.get("title") or "Untitled",
                    "poster_url": tmdb.get("poster_url"),
                }
            )
    return cards


# =============================
# IMPORTANT: Robust TMDB search parsing
# Supports BOTH API shapes:
# 1) raw TMDB: {"results":[{id,title,poster_path,...}]}
# 2) list cards: [{tmdb_id,title,poster_url,...}]
# =============================
def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    """
    Returns:
      suggestions: list[(label, tmdb_id)]
      cards: list[{tmdb_id,title,poster_url}]
    """
    keyword_l = keyword.strip().lower()

    # A) If API returns dict with 'results'
    if isinstance(data, dict) and "results" in data:
        raw = data.get("results") or []
        raw_items = []
        for m in raw:
            title = (m.get("title") or "").strip()
            tmdb_id = m.get("id")
            poster_path = m.get("poster_path")
            if not title or not tmdb_id:
                continue
            raw_items.append(
                {
                    "tmdb_id": int(tmdb_id),
                    "title": title,
                    "poster_url": f"{TMDB_IMG}{poster_path}" if poster_path else None,
                    "release_date": m.get("release_date", ""),
                }
            )

    # B) If API returns already as list
    elif isinstance(data, list):
        raw_items = []
        for m in data:
            # might be {tmdb_id,title,poster_url}
            tmdb_id = m.get("tmdb_id") or m.get("id")
            title = (m.get("title") or "").strip()
            poster_url = m.get("poster_url")
            if not title or not tmdb_id:
                continue
            raw_items.append(
                {
                    "tmdb_id": int(tmdb_id),
                    "title": title,
                    "poster_url": poster_url,
                    "release_date": m.get("release_date", ""),
                }
            )
    else:
        return [], []

    # Word-match filtering (contains)
    matched = [x for x in raw_items if keyword_l in x["title"].lower()]

    # If nothing matched, fallback to raw list (so never blank)
    final_list = matched if matched else raw_items

    # Suggestions = top 10 labels
    suggestions = []
    for x in final_list[:10]:
        year = (x.get("release_date") or "")[:4]
        label = f"{x['title']} ({year})" if year else x["title"]
        suggestions.append((label, x["tmdb_id"]))

    # Cards = top N
    cards = [
        {"tmdb_id": x["tmdb_id"], "title": x["title"], "poster_url": x["poster_url"]}
        for x in final_list[:limit]
    ]
    return suggestions, cards


# =============================
# SIDEBAR (clean)
# =============================
with st.sidebar:
    st.markdown("## 🎬 Menu")
    if st.button("🏠 Home", width='stretch'):
        goto_home()
    if st.button("💖 My Obsessions", width='stretch'):
        goto_watchlist()

    st.markdown("---")
    st.markdown("### 🏠 Home Feed (only home)")
    home_category = st.selectbox(
        "Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"],
        index=0,
    )
    grid_cols = st.slider("Grid columns", 4, 8, 6)

# =============================
# HEADER
# =============================
# =============================
# HEADER
# =============================
st.title("✨ FlixVibe")
st.markdown(
    "<div class='small-muted'>Find your next obsession. No mid recs, just bangers. 🔥</div>",
    unsafe_allow_html=True,
)
st.divider()

# ==========================================================
# VIEW: HOME
# ==========================================================
if st.session_state.view == "home":
    typed = st.text_input(
        "🔍 Search the vibe", placeholder="e.g. Batman, Inception, Dune..."
    )

    st.divider()

    # SEARCH MODE (Autocomplete + word-match results)
    if typed.strip():
        if len(typed.strip()) < 2:
            st.caption("Type at least 2 characters for suggestions.")
        else:
            data, err = api_get_json("/tmdb/search", params={"query": typed.strip()})

            if err or data is None:
                st.error(f"Search failed: {err}")
            else:
                suggestions, cards = parse_tmdb_search_to_cards(
                    data, typed.strip(), limit=24
                )

                # Dropdown
                if suggestions:
                    labels = ["-- Select a movie --"] + [s[0] for s in suggestions]
                    selected = st.selectbox("Suggestions", labels, index=0)

                    if selected != "-- Select a movie --":
                        # map label -> id
                        label_to_id = {s[0]: s[1] for s in suggestions}
                        goto_details(label_to_id[selected])
                else:
                    st.info("No suggestions found. Try another keyword.")

                st.markdown("### Results")
                poster_grid(cards, cols=grid_cols, key_prefix="search_results")

        st.stop()

    # HOME FEED MODE
    st.markdown(f"### 🏠 Home — {home_category.replace('_',' ').title()}")

    home_cards, err = api_get_json(
        "/home", params={"category": home_category, "limit": 24}
    )
    if err or not home_cards:
        st.error(f"Home feed failed: {err or 'Unknown error'}")
        st.stop()

    poster_grid(home_cards, cols=grid_cols, key_prefix="home_feed")

# ==========================================================
# VIEW: DETAILS
# ==========================================================
elif st.session_state.view == "details":
    tmdb_id = st.session_state.selected_tmdb_id
    if not tmdb_id:
        st.warning("No movie selected.")
        if st.button("← Back to Home"):
            goto_home()
        st.stop()

    # Top bar
    a, b = st.columns([3, 1])
    with a:
        st.markdown("### 📄 Movie Details")
    with b:
        if st.button("← Back to Home"):
            goto_home()

    # Watchlist logic functions
    def toggle_watchlist(movie_data):
        current_ids = [m["tmdb_id"] for m in st.session_state.watchlist]
        if movie_data["tmdb_id"] in current_ids:
            st.session_state.watchlist = [
                m for m in st.session_state.watchlist if m["tmdb_id"] != movie_data["tmdb_id"]
            ]
        else:
            st.session_state.watchlist.append({
                "tmdb_id": movie_data["tmdb_id"],
                "title": movie_data["title"],
                "poster_url": movie_data.get("poster_url")
            })

    # Details (your FastAPI safe route)
    data, err = api_get_json(f"/movie/id/{tmdb_id}")
    if err or not data:
        st.error(f"Could not load details: {err or 'Unknown error'}")
        st.stop()

    # Layout: Poster LEFT, Details RIGHT
    left, right = st.columns([1, 2.4], gap="large")

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if data.get("poster_url"):
            st.image(data["poster_url"], width='stretch')
        else:
            st.write("🖼️ No poster")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"## {data.get('title','')}")
        release = data.get("release_date") or "-"
        genres = ", ".join([g["name"] for g in data.get("genres", [])]) or "-"
        st.markdown(
            f"<div class='small-muted'>Release: {release}</div>", unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='small-muted'>Genres: {genres}</div>", unsafe_allow_html=True
        )
        st.markdown("---")
        st.markdown("### Overview")
        st.write(data.get("overview") or "No overview available.")
        
        # Add to Watchlist Button
        is_in_watchlist = data["tmdb_id"] in [m["tmdb_id"] for m in st.session_state.watchlist]
        label = "💔 Remove from Watchlist" if is_in_watchlist else "💖 Add to My Obsessions"
        if st.button(label, width='stretch'):
            toggle_watchlist(data)
            st.rerun()
            
        st.markdown("</div>", unsafe_allow_html=True)

    if data.get("backdrop_url"):
        st.markdown("#### Backdrop")
        st.image(data["backdrop_url"], width='stretch')

    st.divider()
    st.markdown("### ✅ Recommendations")

    # Recommendations (TF-IDF + Genre) via your bundle endpoint
    title = (data.get("title") or "").strip()
    if title:
        bundle, err2 = api_get_json(
            "/movie/search",
            params={"query": title, "tfidf_top_n": 12, "genre_limit": 12},
        )

        if not err2 and bundle:
            st.markdown("#### 🔎 Similar Movies (TF-IDF)")
            poster_grid(
                to_cards_from_tfidf_items(bundle.get("tfidf_recommendations")),
                cols=grid_cols,
                key_prefix="details_tfidf",
            )

            st.markdown("#### 🎭 More Like This (Genre)")
            poster_grid(
                bundle.get("genre_recommendations", []),
                cols=grid_cols,
                key_prefix="details_genre",
            )
        else:
            st.info("Showing Genre recommendations (fallback).")
            genre_only, err3 = api_get_json(
                "/recommend/genre", params={"tmdb_id": tmdb_id, "limit": 18}
            )
            if not err3 and genre_only:
                poster_grid(
                    genre_only, cols=grid_cols, key_prefix="details_genre_fallback"
                )
            else:
                st.warning("No recommendations available right now.")
    else:
        st.warning("No title available for recommendations.")

# ==========================================================
# VIEW: WATCHLIST
# ==========================================================
elif st.session_state.view == "watchlist":
    st.markdown("### 💖 My Obsessions")
    st.markdown("<div class='small-muted'>Your personal collection of bangers.</div>", unsafe_allow_html=True)
    st.divider()
    
    if not st.session_state.watchlist:
        st.info("Your watchlist is empty. Go find some movies to obsess over! 🍿")
        if st.button("Browse Movies"):
            goto_home()
    else:
        # Show watchlist in grid
        poster_grid(st.session_state.watchlist, cols=grid_cols, key_prefix="watchlist_grid")
        
        if st.button("Clear All"):
            st.session_state.watchlist = []
            st.rerun()