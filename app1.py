import streamlit as st
import pickle
import requests
import os
from concurrent.futures import ThreadPoolExecutor

# ===== Function to download a file from GitHub Release =====
def download_from_github(url, dest_path):
    if os.path.exists(dest_path):
        print(f"{dest_path} already exists.")
        return

    print(f"Downloading {dest_path} from GitHub Release...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Check for HTML content (in case of wrong link)
    if "text/html" in response.headers.get("Content-Type", "").lower():
        raise ValueError(f"Invalid file link for {dest_path}. Received HTML instead of binary data.")

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

    print(f"{dest_path} download completed.")

# ===== URLs from GitHub Release (Replace after release creation) =====
MOVIE_URL = "https://github.com/<username>/<repo>/releases/download/<tag>/movie.pkl"
SIMILARITY_URL = "https://github.com/<username>/<repo>/releases/download/<tag>/similarity.pkl"

# ===== Download required files if not present =====
download_from_github(MOVIE_URL, "movie.pkl")
download_from_github(SIMILARITY_URL, "similarity.pkl")

# ===== Load Data =====
movies = pickle.load(open('movie.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

API_KEY = "906192554b54b5439dc8a8f2bc2a3d05"

# ===== Poster Fetching Function =====
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")
        return f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
    except:
        return None

# ===== Recommender =====
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = similarity[index]
    top_indices = sorted(list(enumerate(distances)), key=lambda x: x[1], reverse=True)[1:6]

    recommended_titles = [movies.iloc[i[0]].title for i in top_indices]
    recommended_ids = [movies.iloc[i[0]].movie_id for i in top_indices]

    # Fetch posters in parallel
    with ThreadPoolExecutor() as executor:
        posters = list(executor.map(fetch_poster, recommended_ids))

    return list(zip(recommended_titles, posters))

# ===== Streamlit UI =====
st.set_page_config(layout="wide")
st.title("Movie Recommender System")

selected_movie = st.selectbox("Choose a movie:", movies['title'].values)

if st.button("Recommend"):
    with st.spinner("Finding recommendations..."):
        results = recommend(selected_movie)

    st.write("---")
    st.subheader("Top 5 Recommendations")
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            if results[i][1]:
                st.image(results[i][1], caption=results[i][0], use_container_width=True)
            else:
                st.write(results[i][0])