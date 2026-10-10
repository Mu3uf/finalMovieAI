from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.tools.search_movie import find_tmdb_poster
from app.tools.trending_movies import trending_movies
from app.services.supabase import supabase
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/api/movies",
    tags=["movies"]
)


# ============================================================
# TRENDING
# ============================================================

@router.get("/trending")
def get_trending_movies():

    try:

        result = trending_movies.invoke({
            "number_of_movies": 10
        })

        if not result.get("success"):

            raise HTTPException(
                status_code=500,
                detail=result.get(
                    "message",
                    "Failed to get trending movies."
                )
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# MOVIE ACTION
# ============================================================

class MovieActionRequest(BaseModel):

    imdb_id: str

    liked: Optional[bool] = None

    watched: Optional[bool] = None


@router.post("/action")
def update_movie_action(
    request: MovieActionRequest,
    user=Depends(get_current_user)
):
    try:

        # ----------------------------------------------------
        # Check that movie exists
        # ----------------------------------------------------

        movie_response = (
            supabase
            .table("movies")
            .select("imdb_id")
            .eq("imdb_id", request.imdb_id)
            .limit(1)
            .execute()
        )

        movie_data = movie_response.data or []

        if not movie_data:
            raise HTTPException(
                status_code=404,
                detail="Movie not found."
            )

        # ----------------------------------------------------
        # Get existing action
        # ----------------------------------------------------

        existing_response = (
            supabase
            .table("user_movie_actions")
            .select("liked, watched")
            .eq("user_id", user.id)
            .eq("imdb_id", request.imdb_id)
            .limit(1)
            .execute()
        )

        existing_data = existing_response.data or []

        if existing_data:
            existing = existing_data[0]
        else:
            existing = None

        current_liked = (
            existing.get("liked", False)
            if existing
            else False
        )

        current_watched = (
            existing.get("watched", False)
            if existing
            else False
        )

        # ----------------------------------------------------
        # Only change fields that were supplied
        # ----------------------------------------------------

        liked = (
            request.liked
            if request.liked is not None
            else current_liked
        )

        watched = (
            request.watched
            if request.watched is not None
            else current_watched
        )

        # ----------------------------------------------------
        # If both are false, remove the row
        # ----------------------------------------------------

        if not liked and not watched:

            (
                supabase
                .table("user_movie_actions")
                .delete()
                .eq("user_id", user.id)
                .eq("imdb_id", request.imdb_id)
                .execute()
            )

            return {
                "success": True,
                "imdb_id": request.imdb_id,
                "liked": False,
                "watched": False,
                "message": "Movie action removed."
            }

        # ----------------------------------------------------
        # Upsert
        # ----------------------------------------------------

        (
            supabase
            .table("user_movie_actions")
            .upsert(
                {
                    "user_id": user.id,
                    "imdb_id": request.imdb_id,
                    "liked": liked,
                    "watched": watched
                },
                on_conflict="user_id,imdb_id"
            )
            .execute()
        )

        return {
            "success": True,
            "imdb_id": request.imdb_id,
            "liked": liked,
            "watched": watched,
            "message": "Movie action updated."
        }

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET LIKED MOVIES
# ============================================================

@router.get("/liked")
def get_liked_movies(
    user=Depends(get_current_user)
):

    try:

        actions_response = (
            supabase
            .table("user_movie_actions")
            .select("imdb_id")
            .eq("user_id", user.id)
            .eq("liked", True)
            .execute()
        )

        actions = actions_response.data or []

        imdb_ids = [
            action["imdb_id"]
            for action in actions
        ]

        if not imdb_ids:

            return {
                "success": True,
                "count": 0,
                "movies": []
            }

        movies_response = (
            supabase
            .table("movies")
            .select(
                "imdb_id,"
                "title,"
                "release_year,"
                "rating,"
                "vote_count,"
                "bayesian_score,"
                "genres,"
                "directors,"
                "actors,"
                "poster_path,"
                "duration,"
                "certificate,"
                "status"
            )
            .in_("imdb_id", imdb_ids)
            .execute()
        )

        movies = movies_response.data or []
        for movie in movies:

            if movie.get("poster_path"):
                continue

            poster_path = find_tmdb_poster(
                title=movie.get("title"),
                release_year=movie.get("release_year")
            )

            movie["poster_path"] = poster_path
            # Cache the poster path in Supabase for future requests.
            if poster_path and movie.get("imdb_id"):
                try:
                    (
                        supabase.table("movies")
                        .update({"poster_path": poster_path})
                        .eq("imdb_id", movie["imdb_id"])
                        .execute()
                    )
                except Exception as cache_error:
                    print(f"Could not cache poster: {cache_error}")

        return {
            "success": True,
            "count": len(movies),
            "movies": movies
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET WATCHED MOVIES
# ============================================================

@router.get("/watched")
def get_watched_movies(
    user=Depends(get_current_user)
):

    try:

        actions_response = (
            supabase
            .table("user_movie_actions")
            .select("imdb_id")
            .eq("user_id", user.id)
            .eq("watched", True)
            .execute()
        )

        actions = actions_response.data or []

        imdb_ids = [
            action["imdb_id"]
            for action in actions
        ]

        if not imdb_ids:

            return {
                "success": True,
                "count": 0,
                "movies": []
            }

        movies_response = (
            supabase
            .table("movies")
            .select(
                "imdb_id,"
                "title,"
                "release_year,"
                "rating,"
                "vote_count,"
                "bayesian_score,"
                "genres,"
                "directors,"
                "actors,"
                "poster_path,"
                "duration,"
                "certificate,"
                "status"
            )
            .in_("imdb_id", imdb_ids)
            .execute()
        )

        movies = movies_response.data or []
        for movie in movies:

            if movie.get("poster_path"):
                continue

            poster_path = find_tmdb_poster(
                title=movie.get("title"),
                release_year=movie.get("release_year")
            )

            movie["poster_path"] = poster_path
            # Cache the poster path in Supabase for future requests.
            if poster_path and movie.get("imdb_id"):
                try:
                    (
                        supabase.table("movies")
                        .update({"poster_path": poster_path})
                        .eq("imdb_id", movie["imdb_id"])
                        .execute()
                    )
                except Exception as cache_error:
                    print(f"Could not cache poster: {cache_error}")

        return {
            "success": True,
            "count": len(movies),
            "movies": movies
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )