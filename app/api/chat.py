# ============================================================
# CHAT API
# ============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time
from app.agent.agent import agent

from fastapi import APIRouter, HTTPException, Depends
from app.services.auth import get_current_user
from app.tools.recommend_unwatched_movies import CURRENT_USER_ID
router = APIRouter(
    prefix="/api/chat",
    tags=["chat"]
)


# ============================================================
# REQUEST MODEL
# ============================================================

class ChatRequest(BaseModel):

    message: str


# ============================================================
# EXTRACT MOVIES FROM TOOL RESULTS
# ============================================================

def extract_movies(messages):

    movies = []

    for message in messages:

        # --------------------------------------------------
        # Only inspect tool messages
        # --------------------------------------------------

        if getattr(
            message,
            "type",
            None
        ) != "tool":

            continue

        # --------------------------------------------------
        # NEW: full movie data comes from the artifact
        # --------------------------------------------------

        artifact = getattr(
            message,
            "artifact",
            None
        )

        if isinstance(
            artifact,
            list
        ) and artifact:

            movies.extend(
                artifact
            )

            continue

        content = getattr(
            message,
            "content",
            None
        )

        if not content:

            continue

        # --------------------------------------------------
        # Dictionary result
        # --------------------------------------------------

        if isinstance(
            content,
            dict
        ):

            if content.get(
                "success"
            ):

                tool_movies = content.get(
                    "movies",
                    []
                )

                if tool_movies:

                    movies.extend(
                        tool_movies
                    )

        # --------------------------------------------------
        # JSON string result
        # --------------------------------------------------

        elif isinstance(
            content,
            str
        ):

            try:

                import json

                data = json.loads(
                    content
                )

                if isinstance(
                    data,
                    dict
                ):

                    if data.get(
                        "success"
                    ):

                        tool_movies = data.get(
                            "movies",
                            []
                        )

                        if tool_movies:

                            movies.extend(
                                tool_movies
                            )

            except Exception:

                continue

    # ------------------------------------------------------
    # Remove duplicate movies
    # ------------------------------------------------------

    unique_movies = []

    seen = set()

    for movie in movies:

        movie_key = (
            movie.get("imdb_id")
            or movie.get("tmdb_id")
            or movie.get("title")
        )

        if not movie_key:

            continue

        if movie_key in seen:

            continue

        seen.add(
            movie_key
        )

        unique_movies.append(
            movie
        )

    return unique_movies


# ============================================================
# CHAT ENDPOINT
# ============================================================

@router.post("")
async def chat(
    request: ChatRequest,
    user=Depends(get_current_user),
):

    if not request.message.strip():

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    try:

        # --------------------------------------------------
        # Run agent
        # --------------------------------------------------

        start_time = time.perf_counter()

        token = CURRENT_USER_ID.set(str(user.id))

        try:
            result = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": request.message,
                        }
                    ]
                }
            )
        finally:
            CURRENT_USER_ID.reset(token)

        elapsed = time.perf_counter() - start_time

        elapsed = time.perf_counter() - start_time

        messages = result.get("messages", [])

        print(f"[CHAT DEBUG] Agent time: {elapsed:.2f} seconds")
        print(f"[CHAT DEBUG] Messages returned: {len(messages)}")


        messages = result.get(
            "messages",
            []
        )
        for message in messages:
            print("TYPE:", getattr(message, "type", None))
            print("NAME:", getattr(message, "name", None))
            print("CONTENT:", getattr(message, "content", None))
            print("-" * 50)

        if not messages:

            raise HTTPException(
                status_code=500,
                detail="Agent returned no messages."
            )


        # --------------------------------------------------
        # Extract movies FIRST
        # --------------------------------------------------

        movies = extract_movies(
            messages
        )


        # --------------------------------------------------
        # Get AI response
        # --------------------------------------------------


        final_message = messages[-1]
        final_content = final_message.content

        # Gemini may return content as a list of blocks.
        if isinstance(final_content, list):
            text_parts = []

            for block in final_content:
                if isinstance(block, str):
                    text_parts.append(block)

                elif isinstance(block, dict):
                    if block.get("type") == "text" and block.get("text"):
                        text_parts.append(block["text"])

            final_content = "\n".join(text_parts)

        elif not isinstance(final_content, str):
            final_content = ""


        # --------------------------------------------------
        # Clean response
        #
        # The movie cards already display the movie data.
        # --------------------------------------------------

        if movies:

            final_content = (
                f"I found {len(movies)} "
                f"movie{'s' if len(movies) != 1 else ''} "
                "for you."
            )


        # --------------------------------------------------
        # Return
        # --------------------------------------------------

        return {

            "success": True,

            "message": final_content,

            "movies": movies,

            "count": len(movies)

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