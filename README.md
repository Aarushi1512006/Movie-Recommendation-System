# 🎬 Movie Recommendation System

A modern, hybrid movie recommendation platform that combines **Content-Based Filtering (TF-IDF)** with real-time data from the **TMDB API**. This project features a high-performance **FastAPI** backend and a sleek, interactive **Streamlit** frontend.

---

## 🌟 Features

- **Hybrid Recommendations**: Uses TF-IDF cosine similarity on a local dataset paired with TMDB's genre-based discovery.
- **Real-time Data**: Fetches posters, backdrops, and movie details live from TMDB.
- **Interactive UI**: Modern Streamlit interface with dynamic grids, hover effects, and responsive search.
- **Home Feed**: Explore "Trending", "Popular", "Top Rated", and "Upcoming" movies.
- **Deep Insights**: Detailed movie pages showing overviews, genres, and similar movie suggestions.
- **Fast Performance**: Backend built with FastAPI and vectorized ML models for near-instant results.

---

## 🛠️ Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/)
- **Machine Learning**: Scikit-learn (TF-IDF, Cosine Similarity), Pandas, NumPy
- **API**: [TMDB API (The Movie Database)](https://www.themoviedb.org/documentation/api)
- **Deployment Interface**: Render (API) & Streamlit Cloud (Frontend)

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/MovieRecommendationSystem.git
cd MovieRecommendationSystem
```

### 2. Set up Environment Variables
Create a `.env` file in the root directory and add your TMDB API Key:
```env
TMDB_API_KEY=your_api_key_here
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application

**Option A: Run both (Recommended for Development)**
- Start the Backend:
  ```bash
  uvicorn main:app --reload
  ```
- Start the Frontend:
  ```bash
  streamlit run app.py
  ```

---

## 📂 Project Structure

- `main.py`: FastAPI server handling ML logic and TMDB integration.
- `app.py`: Streamlit application for the user interface.
- `*.pkl`: Serialized dataframes and TF-IDF matrices for the recommendation engine.
- `requirements.txt`: List of Python dependencies.

---

## 🧪 API Endpoints

- `GET /home`: Fetches trending and popular movies.
- `GET /tmdb/search`: Real-time keyword search for movies.
- `GET /movie/search`: Returns details + hybrid recommendations for a specific movie.
- `GET /health`: Basic health check.

---

## 🤝 Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.

## 📝 License
This project is licensed under the MIT License.
