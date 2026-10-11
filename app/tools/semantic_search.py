
import os
import re

import requests
from supabase import create_client
from langchain_core.tools import tool

from app.tools.search_movie import find_tmdb_poster


SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
QUERY_EMBED_SECRET = os.environ["QUERY_EMBED_SECRET"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

EMBEDDING_URL = f"{SUPABASE_URL}/functions/v1/embed-query"


def generate_query_embedding(query: str) -> list[float]:
    """Generate a 384-dimensional embedding for a search query."""

    response = requests.post(
        EMBEDDING_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "apikey": SUPABASE_KEY,
            "x-query-secret": QUERY_EMBED_SECRET,
        },
        json={"query": query},
        timeout=60,
    )

    print("[EMBED STATUS]", response.status_code)
    print("[EMBED RESPONSE]", response.text[:1000])

    response.raise_for_status()

    result = response.json()
    embedding = result.get("embedding")

    if not isinstance(embedding, list) or len(embedding) != 384:
        raise ValueError(
            "The embedding service must return a 384-dimensional vector."
        )

    return embedding


def add_missing_posters(movies: list[dict]) -> list[dict]:
    """Attach existing poster paths and look up missing posters on TMDB."""

    if not movies:
        return movies

    movie_ids = [
        movie["id"]
        for movie in movies
        if movie.get("id") is not None
    ]

    poster_by_id = {}

    if movie_ids:
        try:
            response = (
                supabase.table("movies")
                .select("id, poster_path")
                .in_("id", movie_ids)
                .execute()
            )

            poster_by_id = {
                str(row["id"]): row.get("poster_path")
                for row in (response.data or [])
            }

        except Exception as exc:
            print(f"[POSTER WARNING] Supabase lookup failed: {exc}")

    for movie in movies:
        movie_id = str(movie.get("id", ""))

        movie["poster_path"] = (
            poster_by_id.get(movie_id) or movie.get("poster_path")
        )

        if not movie.get("poster_path"):
            try:
                movie["poster_path"] = find_tmdb_poster(
                    title=movie.get("title"),
                    release_year=movie.get("release_year"),
                )
            except Exception as exc:
                print(
                    f"[POSTER WARNING] Could not find poster for "
                    f"{movie.get('title')}: {exc}"
                )
                movie["poster_path"] = None

    return movies


def extract_reference_title(query: str) -> str | None:
    """Extract the reference movie title from a similar-movie query."""

    query_lower = query.strip().lower()

    patterns = [
        r"\bsimilar\s+movies?\s+to\s+(.+?)\s*[?.!]*$",
        r"\bmovies?\s+similar\s+to\s+(.+?)\s*[?.!]*$",
        r"\bsimilar\s+to\s+(.+?)\s*[?.!]*$",
    ]

    for pattern in patterns:
        match = re.search(pattern, query_lower)

        if match:
            title = match.group(1).strip(" .?!'\"")
            return title or None

    return None


@tool(response_format="content_and_artifact")
def semantic_search(
    query: str,
    number_of_movies: int = 10,
    genre: str | None = None,
    min_rating: float | None = None,
    release_year: int | None = None,
):
    """
    Search for movies using semantic similarity.

    Use for natural-language discovery, mood-based recommendations,
    plot-based searches, and similar-movie requests.

    Args:
        query: Description of the movies the user wants.
        number_of_movies: Number of results, from 1 to 20.
        genre: Optional exact genre, such as Comedy or Horror.
        min_rating: Optional minimum rating.
        release_year: Optional exact release year.

    Returns:
        A concise message for the agent and movie records as an artifact.
        Missing poster paths are looked up using TMDB.
    """

    if not query or not query.strip():
        return (
            "The query cannot be empty.",
            [],
        )

    try:
        count = max(1, min(int(number_of_movies or 10), 20))

        # Detect similar-movie requests and extract the reference title.
        reference_title = extract_reference_title(query)
        is_similar_query = reference_title is not None

        # Fetch an extra candidate so excluding the reference movie
        # can still leave the requested number of results.
        fetch_count = min(count + 1, 20) if is_similar_query else count

        query_embedding = generate_query_embedding(query.strip())

        result = supabase.rpc(
            "match_movies",
            {
                "p_query_embedding": query_embedding,
                "p_match_count": fetch_count,
                "p_genre": genre,
                "p_min_rating": min_rating,
                "p_release_year": release_year,
                "p_min_similarity": 0.0,
            },
        ).execute()

        movies = result.data or []

        # Exclude the reference movie itself from similar-movie results.
        if reference_title:
            movies = [
                movie
                for movie in movies
                if (movie.get("title") or "").strip().lower()
                != reference_title
            ]

        # Never return more movies than requested.
        movies = movies[:count]

        # Add poster paths without regenerating any embeddings.
        movies = add_missing_posters(movies)

        if not movies:
            return (
                "No movies matched the semantic search query. "
                "Do not invent movie results.",
                [],
            )

        
        lines = [
            (
                f"{movie.get('title')} ({movie.get('release_year')}) | "
                f"Rating: {movie.get('rating')} | "
                f"Similarity: {movie.get('similarity')} | "
                f"Genres: {', '.join(movie.get('genres') or [])} | "
                f"Poster: {movie.get('poster_path') or 'Unavailable'}"
            )
            for movie in movies
        ]

        content = (
            f"Found {len(movies)} movies using semantic similarity. "
            "Similarity is a semantic relevance score, not a quality rating. "
            "Use only the returned data; do not invent movie details.\n"
            + "\n".join(lines)
        )

        return content, movies

    except requests.RequestException as exc:
        print(f"[SEMANTIC SEARCH ERROR] RequestException: {exc}")

        return (
            f"The embedding service request failed: {exc}",
            [],
        )

    except Exception as exc:
        print(f"[SEMANTIC SEARCH ERROR] {type(exc).__name__}: {exc}")

        return (
            "Semantic movie search failed due to a technical error. "
            "Do not invent movie results.",
            [],
        )
