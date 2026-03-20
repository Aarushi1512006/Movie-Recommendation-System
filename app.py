import streamlit as st
import pandas as pd
import numpy as np
import ast
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import pickle

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🎬 Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0f0f1a; color: #e0e0e0; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid #2a2a4a;
    }

    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        border: 1px solid #2a2a5a;
        text-align: center;
    }
    .hero h1 { font-size: 2.8rem; margin: 0; color: #fff; font-weight: 800; letter-spacing: -1px; }
    .hero p  { color: #a0a0c0; font-size: 1.1rem; margin-top: 0.5rem; }

    .movie-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        transition: border-color 0.2s, transform 0.2s;
        position: relative;
    }
    .movie-card:hover { border-color: #e94560; transform: translateX(4px); }
    .movie-rank {
        font-size: 0.75rem;
        font-weight: 700;
        color: #e94560;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.3rem;
    }
    .movie-title { font-size: 1.1rem; font-weight: 700; color: #fff; margin-bottom: 0.4rem; }
    .movie-meta  { font-size: 0.85rem; color: #7878a0; }
    .genre-tag {
        display: inline-block;
        background: #0f3460;
        color: #7eb8f7;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.75rem;
        margin: 2px 2px 0 0;
    }
    .rating-badge {
        display: inline-block;
        background: #e94560;
        color: #fff;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-left: 6px;
    }

    .selected-movie {
        background: linear-gradient(135deg, #0f3460, #16213e);
        border: 1px solid #e94560;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .selected-movie h3 { color: #e94560; margin-top: 0; }

    .stat-card {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stat-value { font-size: 1.8rem; font-weight: 800; color: #e94560; }
    .stat-label { font-size: 0.8rem; color: #7878a0; text-transform: uppercase; letter-spacing: 1px; }

    .stSelectbox > div > div, .stTextInput > div > div > input {
        background-color: #1a1a2e !important;
        border-color: #2a2a4a !important;
        color: #e0e0e0 !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #e94560, #c73652);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        width: 100%;
        padding: 0.6rem 1rem;
        font-size: 1rem;
    }
    .stButton > button:hover { background: linear-gradient(135deg, #ff5577, #e94560); }
    .stSlider > div > div > div > div { background: #e94560 !important; }

    .section-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: #e0e0e0;
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e94560;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# ─── NLTK Setup ─────────────────────────────────────────────────────────────────
@st.cache_resource
def load_nltk():
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    return set(stopwords.words('english')), WordNetLemmatizer()

stop_words, lemmatizer = load_nltk()


# ─── Preprocessing ──────────────────────────────────────────────────────────────
def preprocess_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    words = text.split()
    words = [w for w in words if w not in stop_words]
    words = [lemmatizer.lemmatize(w) for w in words]
    return " ".join(words)


# ─── Data Loading & Model Building ──────────────────────────────────────────────
CACHE_FILES = ['df.pkl', 'tfidf_matrix.pkl', 'indices.pkl', 'tfidf.pkl']

@st.cache_resource(show_spinner=False)
def build_model(csv_path):
    if all(os.path.exists(f) for f in CACHE_FILES):
        df         = pd.read_pickle('df.pkl')
        tfidf_mat  = pickle.load(open('tfidf_matrix.pkl', 'rb'))
        indices    = pickle.load(open('indices.pkl', 'rb'))
        tfidf      = pickle.load(open('tfidf.pkl', 'rb'))
        return df, tfidf_mat, indices, tfidf

    df = pd.read_csv(csv_path, low_memory=False)
    df = df.drop_duplicates().reset_index(drop=True)
    df = df[['title', 'overview', 'genres', 'tagline', 'vote_average', 'popularity']]
    df = df.dropna(subset=['title'])
    df['overview']  = df['overview'].fillna(' ')
    df['tagline']   = df['tagline'].fillna(' ')
    df['genres']    = df['genres'].apply(
        lambda x: " ".join([i['name'] for i in ast.literal_eval(x)]) if x and x != '[]' else ''
    )
    df['tags'] = df['overview'] + " " + df['genres'] + " " + df['tagline']
    df['tags'] = df['tags'].apply(preprocess_text)
    df = df.reset_index(drop=True)
    df['vote_average'] = pd.to_numeric(df['vote_average'], errors='coerce').fillna(0)
    df['popularity']   = pd.to_numeric(df['popularity'],   errors='coerce').fillna(0)

    indices = pd.Series(df.index, index=df['title']).drop_duplicates()

    tfidf     = TfidfVectorizer(max_features=50000, ngram_range=(1, 2), stop_words='english')
    tfidf_mat = tfidf.fit_transform(df['tags'])
    
    df.to_pickle('df.pkl')
    pickle.dump(tfidf_mat, open('tfidf_matrix.pkl', 'wb'))
    pickle.dump(indices, open('indices.pkl', 'wb'))
    pickle.dump(tfidf, open('tfidf.pkl', 'wb'))

    return df, tfidf_mat, indices, tfidf


def recommend(title, df, tfidf_mat, indices, n=10):
    if title not in indices:
        return pd.DataFrame()
    idx       = indices[title]
    sim_score = cosine_similarity(tfidf_mat[idx], tfidf_mat).flatten()
    sim_score[idx] = 0
    similar_idx = sim_score.argsort()[::-1][:n]
    results   = df.iloc[similar_idx][['title', 'genres', 'vote_average', 'popularity', 'overview', 'tagline']].copy()
    results['similarity'] = sim_score[similar_idx]
    return results.reset_index(drop=True)


# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    uploaded = st.file_uploader(
        "Upload movies_metadata.csv",
        type=['csv'],
        help="Upload the TMDB movies_metadata.csv file"
    )

    st.markdown("---")
    n_recs = st.slider("Number of recommendations", 5, 20, 10)
    min_rating = st.slider("Minimum vote average", 0.0, 10.0, 0.0, 0.5)

    st.markdown("---")
    st.markdown("### 🎯 About")
    st.markdown(
        "Content-based recommender using **TF-IDF** vectorization and "
        "**cosine similarity** on movie overviews, genres, and taglines.",
        unsafe_allow_html=True
    )


# ─── Hero Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🎬 Movie Recommender</h1>
    <p>Discover films similar to the ones you love — powered by NLP & cosine similarity</p>
</div>
""", unsafe_allow_html=True)


# ─── Main Logic ─────────────────────────────────────────────────────────────────
csv_path = None
if uploaded:
    tmp_path = f"/tmp/{uploaded.name}"
    with open(tmp_path, 'wb') as f:
        f.write(uploaded.read())
    csv_path = tmp_path
elif os.path.exists('movies_metadata.csv'):
    csv_path = 'movies_metadata.csv'

if csv_path is None:
    st.info("👈 Upload **movies_metadata.csv** in the sidebar to get started.", icon="📂")
    st.stop()

with st.spinner("🔄 Loading dataset and building model... (first run may take a minute)"):
    df, tfidf_mat, indices, tfidf = build_model(csv_path)

# Dataset stats
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{len(df):,}</div>
        <div class="stat-label">Movies</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{tfidf_mat.shape[1]:,}</div>
        <div class="stat-label">TF-IDF Features</div>
    </div>""", unsafe_allow_html=True)
with col3:
    avg = df['vote_average'].mean()
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{avg:.1f}</div>
        <div class="stat-label">Avg Rating</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Search ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔍 Find a Movie</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

all_titles = sorted(df['title'].dropna().unique().tolist())
selected   = st.selectbox(
    "Type or select a movie title",
    options=[""] + all_titles,
    index=0,
    placeholder="e.g. Avatar, Toy Story, Inception..."
)

col_btn, col_space = st.columns([1, 3])
with col_btn:
    get_recs = st.button("🎯 Get Recommendations")

# ─── Results ────────────────────────────────────────────────────────────────────
if get_recs and selected:
    movie_info = df[df['title'] == selected]
    if not movie_info.empty:
        m = movie_info.iloc[0]
        st.markdown(f"""
        <div class="selected-movie">
            <h3>📽️ {m['title']}</h3>
            <p style="color:#a0a0c0; margin:0.3rem 0">{m['overview'][:280]}{'...' if len(str(m['overview'])) > 280 else ''}</p>
            <p style="margin-top:0.8rem">
                {''.join(f'<span class="genre-tag">{g.strip()}</span>' for g in str(m['genres']).split() if g.strip())}
                <span class="rating-badge">⭐ {m['vote_average']:.1f}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with st.spinner("🔍 Finding similar movies..."):
        results = recommend(selected, df, tfidf_mat, indices, n=50)

    if results.empty:
        st.error("Movie not found in the database. Please try another title.")
    else:
        results = results[results['vote_average'] >= min_rating].head(n_recs)

        if results.empty:
            st.warning(f"No movies found with rating ≥ {min_rating}. Try lowering the filter.")
        else:
            st.markdown(
                f'<div class="section-header">🎞️ Top {len(results)} Recommendations</div>',
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)

            left, right = st.columns(2)
            for i, (_, row) in enumerate(results.iterrows()):
                genres_html = ''.join(
                    f'<span class="genre-tag">{g.strip()}</span>'
                    for g in str(row['genres']).split() if g.strip()
                )
                overview_snippet = str(row['overview'])[:160] + ('...' if len(str(row['overview'])) > 160 else '')
                sim_pct = int(row['similarity'] * 100)

                card = f"""
                <div class="movie-card">
                    <div class="movie-rank">#{i+1} &nbsp;·&nbsp; {sim_pct}% match</div>
                    <div class="movie-title">{row['title']}
                        <span class="rating-badge">⭐ {row['vote_average']:.1f}</span>
                    </div>
                    <div style="margin:0.4rem 0">{genres_html}</div>
                    <div class="movie-meta">{overview_snippet}</div>
                </div>
                """
                if i % 2 == 0:
                    left.markdown(card, unsafe_allow_html=True)
                else:
                    right.markdown(card, unsafe_allow_html=True)

elif get_recs and not selected:
    st.warning("Please select a movie first.")

elif not get_recs:
    st.markdown("""
    <div style="text-align:center; color:#4a4a7a; padding: 3rem 0;">
        <div style="font-size:4rem">🎥</div>
        <div style="font-size:1.1rem; margin-top:0.5rem">Select a movie and click <b>Get Recommendations</b></div>
    </div>
    """, unsafe_allow_html=True)
