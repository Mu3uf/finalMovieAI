# ============================================================
# MOVIE SEARCH TOOL
# ============================================================

import os
import traceback
import requests

from functools import lru_cache

from langchain_core.tools import tool
from dotenv import load_dotenv

from app.services.supabase import supabase


# ------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY is missing from .env")


# ------------------------------------------------------------
# TMDB configuration
# ------------------------------------------------------------

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"


# ============================================================
# INPUT CLEANING
# ============================================================
# Some LLMs (for example Gemini) fill optional tool parameters with
# placeholders such as 0, "", "null" or "None" instead of leaving
# them empty. A placeholder like release_year=0 or rating_max=0
# would filter out every movie, so every value is cleaned here and
# anything that is not a real value becomes None (= filter ignored).
# ============================================================

_EMPTY_STRINGS = {
    "", "null", "none", "n/a", "na", "nan", "undefined", "any", "unknown"
}


def clean_text(value):
    """Return a stripped string, or None if the value is empty/placeholder."""

    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    if value.lower() in _EMPTY_STRINGS:
        return None

    return value


def _to_number(value):
    """Convert a value to float, or None if it is not a real number."""

    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, str):

        value = value.strip()

        if value.lower() in _EMPTY_STRINGS:
            return None

    try:
        number = float(value)
    except (ValueError, TypeError):
        return None

    if number != number or number in (float("inf"), float("-inf")):
        return None

    return number


def clean_positive_int(value):
    """Return an int > 0, or None (0, negatives and placeholders = not set)."""

    number = _to_number(value)

    if number is None or number <= 0:
        return None

    return int(number)


def clean_positive_float(value):
    """Return a float > 0, or None (0, negatives and placeholders = not set)."""

    number = _to_number(value)

    if number is None or number <= 0:
        return None

    return number


# ============================================================
# COMPACT TEXT FOR THE LLM
# ============================================================

def compact_for_llm(movies):
    """Short text version for the LLM. The UI gets the full data via artifact."""
    lines = []
    for m in movies:
        genres = m.get("genres") or []
        if isinstance(genres, list):
            genres = ", ".join(genres[:3])
        lines.append(
            f"{m.get('title')} ({m.get('release_year')}) "
            f"rating {m.get('rating')} | {genres}"
        )
    return (
        f"Found {len(movies)} movies. Movie cards are displayed "
        "to the user automatically; do not repeat details.\n"
        + "\n".join(lines)
    )


# ============================================================
# TMDB POSTER SEARCH
# ============================================================

@lru_cache(maxsize=2000)
def find_tmdb_poster(
    title: str,
    release_year: int = None
):
    """
    Search for a movie in TMDB using its title and release year.

    Returns:
        poster_path if a suitable TMDB movie is found.
        None otherwise.
    """

    if not title:
        return None

    try:

        # ----------------------------------------------------
        # Search TMDB by movie title
        # ----------------------------------------------------

        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "include_adult": "false",
            "language": "en-US",
            "page": 1
        }

        response = requests.get(
            TMDB_SEARCH_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        if not results:
            return None


        # ----------------------------------------------------
        # Prefer exact release year match
        # ----------------------------------------------------

        if release_year is not None:

            year_matches = []

            for movie in results:

                release_date = movie.get("release_date")

                if not release_date:
                    continue

                try:
                    tmdb_year = int(
                        release_date[:4]
                    )
                except (ValueError, TypeError):
                    continue

                if tmdb_year == release_year:
                    year_matches.append(movie)


            # ------------------------------------------------
            # Exact year + poster
            # ------------------------------------------------

            for movie in year_matches:

                poster_path = movie.get("poster_path")

                if poster_path:
                    return poster_path


            # ------------------------------------------------
            # Exact year found but no poster
            # ------------------------------------------------

            if year_matches:
                return None


        # ----------------------------------------------------
        # Fallback to first result with a poster
        # ----------------------------------------------------

        for movie in results:

            poster_path = movie.get("poster_path")

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


# ============================================================
# SEARCH LOGIC (called by the tool below)
# ============================================================

def _run_search(
    title,
    genre,
    actor,
    director,
    release_year,
    release_year_min,
    release_year_max,
    rating_min,
    rating_max,
    vote_count_min,
    number_of_movies
):
    """Clean the inputs, build the Supabase query and return (text, movies)."""

    # --------------------------------------------------
    # Clean every input: only real user values survive,
    # everything else becomes None (= filter not applied)
    # --------------------------------------------------

    title = clean_text(title)
    genre = clean_text(genre)
    actor = clean_text(actor)
    director = clean_text(director)

    release_year = clean_positive_int(release_year)
    release_year_min = clean_positive_int(release_year_min)
    release_year_max = clean_positive_int(release_year_max)

    rating_min = clean_positive_float(rating_min)
    rating_max = clean_positive_float(rating_max)

    vote_count_min = clean_positive_int(vote_count_min)

    number_of_movies = clean_positive_int(number_of_movies)

    # Not provided (or placeholder) -> default of 10
    if number_of_movies is None:
        number_of_movies = 10


    # --------------------------------------------------
    # Validate number of movies
    # --------------------------------------------------

    if number_of_movies > 50:
        return "number_of_movies must be an integer between 1 and 50.", []


    # --------------------------------------------------
    # Debug: what the search will really use
    # --------------------------------------------------

    print(
        "[SEARCH DEBUG] cleaned filters -> "
        f"title={title} genre={genre} actor={actor} director={director} "
        f"year={release_year} year_min={release_year_min} "
        f"year_max={release_year_max} rating_min={rating_min} "
        f"rating_max={rating_max} vote_count_min={vote_count_min} "
        f"n={number_of_movies}"
    )


    # --------------------------------------------------
    # Select columns
    # --------------------------------------------------

    query = supabase.table("movies").select(
        "imdb_id,"
        "title,"
        "release_year,"
        "rating,"
        "vote_count,"
        "bayesian_score,"
        "genres,"
        "directors,"
        "actors,"
        "keywords,"
        "plot,"
        "poster_path,"
        "duration,"
        "certificate,"
        "country,"
        "language,"
        "status"
    )

    active_filters = []


    # --------------------------------------------------
    # Title filter
    # --------------------------------------------------

    if title:

        query = query.ilike(
            "title",
            f"%{title}%"
        )

        active_filters.append(f"title~{title}")


    # --------------------------------------------------
    # Genre filter
    # --------------------------------------------------

    if genre:

        genre = genre.strip().title()

        query = query.contains(
            "genres",
            [genre]
        )

        active_filters.append(f"genre={genre}")


    # --------------------------------------------------
    # Actor filter
    # --------------------------------------------------

    if actor:

        query = query.contains(
            "actors",
            [actor]
        )

        active_filters.append(f"actor={actor}")


    # --------------------------------------------------
    # Director filter
    # --------------------------------------------------

    if director:

        query = query.contains(
            "directors",
            [director]
        )

        active_filters.append(f"director={director}")


    # --------------------------------------------------
    # Exact release year
    # --------------------------------------------------

    if release_year is not None:

        query = query.eq(
            "release_year",
            release_year
        )

        active_filters.append(f"release_year={release_year}")


    # --------------------------------------------------
    # Minimum release year
    # --------------------------------------------------

    if release_year_min is not None:

        query = query.gte(
            "release_year",
            release_year_min
        )

        active_filters.append(f"release_year>={release_year_min}")


    # --------------------------------------------------
    # Maximum release year
    # --------------------------------------------------

    if release_year_max is not None:

        query = query.lte(
            "release_year",
            release_year_max
        )

        active_filters.append(f"release_year<={release_year_max}")


    # --------------------------------------------------
    # Minimum rating
    # --------------------------------------------------

    if rating_min is not None:

        query = query.gte(
            "rating",
            rating_min
        )

        active_filters.append(f"rating>={rating_min}")


    # --------------------------------------------------
    # Maximum rating
    # --------------------------------------------------

    if rating_max is not None:

        query = query.lte(
            "rating",
            rating_max
        )

        active_filters.append(f"rating<={rating_max}")


    # --------------------------------------------------
    # Minimum vote count
    # --------------------------------------------------

    if vote_count_min is not None:

        query = query.gte(
            "vote_count",
            vote_count_min
        )

        active_filters.append(f"vote_count>={vote_count_min}")


    # --------------------------------------------------
    # Rank by Bayesian score
    # --------------------------------------------------

    query = query.order(
        "bayesian_score",
        desc=True
    )

    query = query.order(
        "rating",
        desc=True
    )

    query = query.order(
        "vote_count",
        desc=True
    )


    # --------------------------------------------------
    # Limit results
    # --------------------------------------------------

    query = query.limit(
        number_of_movies
    )


    # --------------------------------------------------
    # Execute
    # --------------------------------------------------

    response = query.execute()

    movies = response.data or []

    print(f"[SEARCH DEBUG] rows returned: {len(movies)}")


    # --------------------------------------------------
    # No results
    # --------------------------------------------------

    if not movies:

        # No filter was applied and still nothing came back:
        # this is not a search problem, it is a database access
        # problem (RLS policy, wrong API key, empty/paused DB).
        if not active_filters:

            print(
                "[SEARCH WARNING] The movies table returned 0 rows "
                "with NO filters. Check the Supabase RLS policy on "
                "'movies', the SUPABASE key used on this server, and "
                "that the project is not paused."
            )

            return (
                "TOOL ERROR: the movies table returned no rows even "
                "without any filter. This is a database access problem, "
                "not a search problem. Tell the user a temporary technical "
                "problem occurred and ask them to try again later. "
                "Do NOT invent or guess any movies.",
                []
            )

        return (
            "No movies matched the requested filters "
            f"({', '.join(active_filters)}).",
            []
        )


    # ==================================================
    # CHECK POSTERS
    # ==================================================

    for movie in movies:

        # ------------------------------------------------
        # Poster already exists
        # ------------------------------------------------

        if movie.get("poster_path"):
            continue


        # ------------------------------------------------
        # Poster missing
        # ------------------------------------------------

        movie_title = movie.get("title")
        movie_year = movie.get("release_year")


        # ------------------------------------------------
        # Search TMDB
        # ------------------------------------------------

        poster_path = find_tmdb_poster(
            title=movie_title,
            release_year=movie_year
        )


        # ------------------------------------------------
        # Add poster path to returned result
        # ------------------------------------------------

        movie["poster_path"] = poster_path


    # --------------------------------------------------
    # Success
    # --------------------------------------------------

    return compact_for_llm(movies), movies


# ============================================================
# SEARCH MOVIE TOOL
# ============================================================

@tool(response_format="content_and_artifact")
def search_movie(
    title: str = None,
    genre: str = None,
    actor: str = None,
    director: str = None,
    release_year: int = None,
    release_year_min: int = None,
    release_year_max: int = None,
    rating_min: float = None,
    rating_max: float = None,
    vote_count_min: int = None,
    number_of_movies: int = 10
):
    """
    Search movies from the Supabase movie database.

    Filters:
    - title
    - genre
    - actor
    - director
    - release year
    - rating
    - vote count

    IMPORTANT: every filter is optional. Only fill a filter if the user
    explicitly asked for it. Leave all other filters empty (null).
    Never use 0, an empty string, "null" or "none" as a placeholder.
    If the user asks for movies without any condition, call the tool
    with no filters and only number_of_movies.

    Results are ranked using Bayesian score.

    If a movie does not have a poster_path in Supabase,
    search TMDB using the movie title and release year
    to find its poster.
    """

    # --------------------------------------------------
    # Debug: raw values exactly as the LLM sent them
    # --------------------------------------------------

    print(
        "[TOOL DEBUG] raw args -> "
        f"title={title!r} genre={genre!r} actor={actor!r} "
        f"director={director!r} release_year={release_year!r} "
        f"release_year_min={release_year_min!r} "
        f"release_year_max={release_year_max!r} "
        f"rating_min={rating_min!r} rating_max={rating_max!r} "
        f"vote_count_min={vote_count_min!r} "
        f"number_of_movies={number_of_movies!r}"
    )


    # --------------------------------------------------
    # Run the search. Any failure returns a clear message
    # to the agent instead of crashing the chat.
    # --------------------------------------------------

    try:

        return _run_search(
            title=title,
            genre=genre,
            actor=actor,
            director=director,
            release_year=release_year,
            release_year_min=release_year_min,
            release_year_max=release_year_max,
            rating_min=rating_min,
            rating_max=rating_max,
            vote_count_min=vote_count_min,
            number_of_movies=number_of_movies
        )

    except Exception as e:

        print(f"[SEARCH ERROR] {type(e).__name__}: {e}")
        traceback.print_exc()

        return (
            "TOOL ERROR: the movie search tool failed "
            f"({type(e).__name__}: {e}). "
            "Tell the user a temporary technical problem occurred while "
            "searching the movie database and ask them to try again later. "
            "Do NOT invent or guess any movies.",
            []
        )