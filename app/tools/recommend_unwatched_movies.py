import os
import asyncio
import traceback
from contextvars import ContextVar
from functools import lru_cache

import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
from supabase import create_client

load_dotenv()

CURRENT_USER_ID = ContextVar("CURRENT_USER_ID", default=None)

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"

BATCH_SIZE = 100
MAX_MOVIES = 50
WATCHED_PAGE_SIZE = 500

MOVIE_COLUMNS = (
    "imdb_id,title,release_year,rating,vote_count,bayesian_score,"
    "genres,directors,actors,keywords,plot,poster_path,duration,"
    "certificate,country,language,status"
)

_supabase = None


# ============================================================
# SUPABASE CLIENT (created on first use, never crashes startup)
# ============================================================

def _get_supabase():
    global _supabase

    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is missing")

        _supabase = create_client(url, key)

    return _supabase


# ============================================================
# WATCHED MOVIES  (table: user_movie_actions)
# ============================================================

def _get_watched_imdb_ids(user_id: str) -> set[str]:
    supabase = _get_supabase()

    watched = set()
    offset = 0

    while True:
        response = (
            supabase.table("user_movie_actions")
            .select("imdb_id")
            .eq("user_id", user_id)
            .eq("watched", True)
            .range(offset, offset + WATCHED_PAGE_SIZE - 1)
            .execute()
        )

        rows = response.data or []

        for row in rows:
            imdb_id = row.get("imdb_id")
            if imdb_id:
                watched.add(str(imdb_id).strip())

        if len(rows) < WATCHED_PAGE_SIZE:
            break

        offset += len(rows)

    return watched


# ============================================================
# TMDB POSTER FALLBACK
# ============================================================

@lru_cache(maxsize=2000)
def _find_tmdb_poster(title: str, release_year: int | None = None):
    api_key = os.getenv("TMDB_API_KEY")

    if not title or not api_key:
        return None

    try:
        response = requests.get(
            TMDB_SEARCH_URL,
            params={
                "api_key": api_key,
                "query": title,
                "include_adult": "false",
                "language": "en-US",
                "page": 1,
            },
            timeout=10,
        )
        response.raise_for_status()
        results = response.json().get("results", [])

        if release_year is not None:
            for movie in results:
                date = movie.get("release_date") or ""
                try:
                    year = int(date[:4])
                except ValueError:
                    continue
                if year == release_year and movie.get("poster_path"):
                    return movie["poster_path"]

        for movie in results:
            if movie.get("poster_path"):
                return movie["poster_path"]

    except requests.RequestException as exc:
        print(f"[POSTER ERROR] {title}: {exc}")

    return None


# ============================================================
# MOVIE QUERY
# ============================================================

def _build_query(
    genre, actor, director, release_year, year_min, year_max,
    rating_min, rating_max, min_vote_count, offset,
):
    query = _get_supabase().table("movies").select(MOVIE_COLUMNS)

    if genre:
        query = query.contains("genres", [genre])

    if actor:
        query = query.contains("actors", [actor])

    if director:
        query = query.contains("directors", [director])

    if release_year is not None:
        query = query.eq("release_year", release_year)

    if year_min is not None:
        query = query.gte("release_year", year_min)

    if year_max is not None:
        query = query.lte("release_year", year_max)

    if rating_min is not None:
        query = query.gte("rating", rating_min)

    if rating_max is not None:
        query = query.lte("rating", rating_max)

    if min_vote_count is not None:
        query = query.gte("vote_count", min_vote_count)

    query = (
        query.order("bayesian_score", desc=True)
        .order("rating", desc=True)
        .order("vote_count", desc=True)
        .range(offset, offset + BATCH_SIZE - 1)
    )

    return query


# ============================================================
# SEARCH (blocking; runs in a worker thread)
# ============================================================

def _search_unwatched(
    user_id, genre, actor, director, release_year, year_min, year_max,
    rating_min, rating_max, min_vote_count, number_of_movies,
):
    watched = _get_watched_imdb_ids(user_id)

    selected = []
    seen = set()
    offset = 0

    while len(selected) < number_of_movies:
        batch = (
            _build_query(
                genre, actor, director, release_year, year_min, year_max,
                rating_min, rating_max, min_vote_count, offset,
            )
            .execute()
            .data
            or []
        )

        if not batch:
            break

        for movie in batch:
            imdb_id = str(movie.get("imdb_id") or "").strip()

            if not imdb_id or imdb_id in watched or imdb_id in seen:
                continue

            seen.add(imdb_id)
            selected.append(movie)

            if len(selected) >= number_of_movies:
                break

        offset += len(batch)

        if len(batch) < BATCH_SIZE:
            break

    for movie in selected:
        if not movie.get("poster_path"):
            movie["poster_path"] = _find_tmdb_poster(
                movie.get("title"),
                movie.get("release_year"),
            )

    print(
        f"[UNWATCHED] watched={len(watched)} "
        f"returned={len(selected)} (n={number_of_movies})"
    )

    return selected


def _format_for_llm(movies) -> str:
    lines = []

    for movie in movies:
        genres = movie.get("genres") or []
        if isinstance(genres, list):
            genres = ", ".join(str(g) for g in genres[:3])

        lines.append(
            f"{movie.get('title')} ({movie.get('release_year')}) "
            f"rating {movie.get('rating')} | {genres}"
        )

    return (
        f"Found {len(movies)} unwatched movies. "
        "Movie cards are displayed to the user automatically; "
        "do not repeat details.\n" + "\n".join(lines)
    )


# ============================================================
# LANGCHAIN TOOL
# ============================================================

@tool(response_format="content_and_artifact")
async def recommend_unwatched_movies(
    genre: str = "",
    actor: str = "",
    director: str = "",
    release_year: int | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    rating_min: float | None = None,
    rating_max: float | None = None,
    min_vote_count: int | None = None,
    number_of_movies: int = 10,
) -> tuple[str, list]:
    """
    Recommend movies the authenticated user has not watched.

    Use this tool when the user requests movies they have not
    watched or seen before.

    Supports genre, actor, director, release year, year range,
    minimum/maximum rating, minimum vote count, and movie count.

    The authenticated user ID is obtained from server context.
    Never invent a user ID or claim a movie is unwatched without
    confirmation from the tool results.
    """

    user_id = CURRENT_USER_ID.get()

    if not user_id:
        return (
            "Cannot recommend unwatched movies without "
            "an authenticated user ID.",
            [],
        )

    if not 1 <= number_of_movies <= MAX_MOVIES:
        return f"number_of_movies must be between 1 and {MAX_MOVIES}.", []

    try:
        movies = await asyncio.to_thread(
            _search_unwatched,
            str(user_id).strip(),
            genre.strip() or None,
            actor.strip() or None,
            director.strip() or None,
            release_year,
            year_min,
            year_max,
            rating_min,
            rating_max,
            min_vote_count,
            number_of_movies,
        )
    except Exception:
        traceback.print_exc()
        return "Movie recommendation failed. Please try again.", []

    if not movies:
        return "No unwatched movies matched the requested filters.", []

    return _format_for_llm(movies), movies