# ============================================================
# TMDB SERVICE
# ============================================================

import os
import requests

from dotenv import load_dotenv


load_dotenv()


TMDB_API_KEY = os.getenv("TMDB_API_KEY")


if not TMDB_API_KEY:
    raise ValueError(
        "TMDB_API_KEY is missing from .env"
    )


TMDB_BASE_URL = "https://api.themoviedb.org/3"

TMDB_IMAGE_BASE_URL = (
    "https://image.tmdb.org/t/p/w500"
)


def find_tmdb_poster(
    title: str,
    release_year: int = None
):
    """
    Search TMDB for a movie poster.

    Returns:
        poster_path or None
    """

    if not title:
        return None

    url = f"{TMDB_BASE_URL}/search/movie"

    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "include_adult": "false",
        "language": "en-US",
        "page": 1
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get(
            "results",
            []
        )

        if not results:
            return None

        # --------------------------------------------------
        # Try matching release year
        # --------------------------------------------------

        if release_year is not None:

            year_matches = []

            for movie in results:

                release_date = movie.get(
                    "release_date"
                )

                if not release_date:
                    continue

                try:

                    tmdb_year = int(
                        release_date[:4]
                    )

                except (
                    ValueError,
                    TypeError
                ):
                    continue

                if tmdb_year == release_year:

                    year_matches.append(
                        movie
                    )

            for movie in year_matches:

                poster_path = movie.get(
                    "poster_path"
                )

                if poster_path:

                    return poster_path

            if year_matches:

                return None

        # --------------------------------------------------
        # Fallback
        # --------------------------------------------------

        for movie in results:

            poster_path = movie.get(
                "poster_path"
            )

            if poster_path:

                return poster_path

        return None

    except requests.RequestException as e:

        print(
            f"TMDB request failed for '{title}': {e}"
        )

        return None

    except Exception as e:

        print(
            f"TMDB poster search error for '{title}': {e}"
        )

        return None


def get_poster_url(
    poster_path: str
):
    """
    Convert TMDB poster_path into a complete image URL.
    """

    if not poster_path:
        return None

    if poster_path.startswith("http"):

        return poster_path

    return (
        f"{TMDB_IMAGE_BASE_URL}"
        f"{poster_path}"
    )