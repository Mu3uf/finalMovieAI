import os
import requests

from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY is missing from .env")

TMDB_TRENDING_URL = "https://api.themoviedb.org/3/trending/movie/day"
TMDB_EXTERNAL_IDS_URL = "https://api.themoviedb.org/3/movie/{tmdb_id}/external_ids"



@tool
def trending_movies(number_of_movies: int = 10):
    """
    Get the current trending movies from TMDB.
    Returns movie title, rating, release date, overview,
    poster path, and IMDb ID.
    """
    number_of_movies = max(1, min(number_of_movies, 20))

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "page": 1
    }

    try:
        response = requests.get(
            TMDB_TRENDING_URL,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            return {
                "success": False,
                "count": 0,
                "movies": [],
                "message": "No trending movies found."
            }

        movies = []

        for movie in results[:number_of_movies]:

            tmdb_id = movie.get("id")
            imdb_id = None

            if tmdb_id:
                try:
                    external_response = requests.get(
                        TMDB_EXTERNAL_IDS_URL.format(tmdb_id=tmdb_id),
                        params={"api_key": TMDB_API_KEY},
                        timeout=10
                    )

                    external_response.raise_for_status()

                    external_data = external_response.json()
                    imdb_id = external_data.get("imdb_id")

                except requests.RequestException as e:
                    print(
                        f"TMDB external ID request failed "
                        f"for movie {tmdb_id}: {e}"
                    )

            movies.append({
                "tmdb_id": tmdb_id,
                "imdb_id": imdb_id,
                "title": movie.get("title"),
                "release_date": movie.get("release_date"),
                "rating": movie.get("vote_average"),
                "vote_count": movie.get("vote_count"),
                "overview": movie.get("overview"),
                "poster_path": movie.get("poster_path"),
                "backdrop_path": movie.get("backdrop_path"),
                "original_language": movie.get("original_language"),
                "popularity": movie.get("popularity")
            })

        return {
            "success": True,
            "count": len(movies),
            "movies": movies,
            "message": f"Found {len(movies)} trending movies."
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "count": 0,
            "movies": [],
            "message": f"TMDB request failed: {str(e)}"
        }

    except Exception as e:
        return {
            "success": False,
            "count": 0,
            "movies": [],
            "message": f"Unexpected error: {str(e)}"
        }