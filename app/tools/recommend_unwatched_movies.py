
import os
import json
import httpx

from contextvars import ContextVar
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from langchain_core.tools import tool

load_dotenv()

CURRENT_USER_ID = ContextVar("CURRENT_USER_ID", default=None)

MCP_SERVER_URL = os.environ["MCP_SERVER_URL"]


@tool
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
) -> str:
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

    # Get the authenticated user's ID from server context.
    user_id = CURRENT_USER_ID.get()

    if not user_id:
        return (
            "Cannot recommend unwatched movies without "
            "an authenticated user ID."
        )

    if not 1 <= number_of_movies <= 50:
        return "number_of_movies must be between 1 and 50."

    arguments = {
        "user_id": user_id,
        "number_of_movies": number_of_movies,
    }

    optional_filters = {
        "genre": genre,
        "actor": actor,
        "director": director,
        "release_year": release_year,
        "year_min": year_min,
        "year_max": year_max,
        "rating_min": rating_min,
        "rating_max": rating_max,
        "min_vote_count": min_vote_count,
    }

    arguments.update({
        key: value
        for key, value in optional_filters.items()
        if value is not None and value != ""
    })

    try:
        timeout = httpx.Timeout(
            90.0,
            connect=90.0,
        )

        async with httpx.AsyncClient(
            timeout=timeout,
        ) as http_client:

            async with streamable_http_client(
                MCP_SERVER_URL,
                http_client=http_client,
            ) as (
                read_stream,
                write_stream,
                _,
            ):

                async with ClientSession(
                    read_stream,
                    write_stream,
                ) as session:

                    await session.initialize()

                    available = await session.list_tools()

                    remote_tool = next(
                        (
                            item
                            for item in available.tools
                            if item.name == "recommend_unwatched_movies"
                        ),
                        None,
                    )

                    if remote_tool is None:
                        return (
                            "The remote MCP server does not expose "
                            "recommend_unwatched_movies."
                        )

                    # Send only parameters accepted by the MCP tool.
                    properties = (
                        remote_tool.inputSchema.get("properties", {})
                    )

                    accepted_arguments = {
                        key: value
                        for key, value in arguments.items()
                        if key in properties
                    }

                    result = await session.call_tool(
                        "recommend_unwatched_movies",
                        arguments=accepted_arguments,
                    )

                    if result.isError:
                        return (
                            "The movie recommendation service "
                            "returned an error."
                        )

                    text_parts = [
                        item.text
                        for item in result.content
                        if getattr(item, "type", None) == "text"
                    ]

                    if text_parts:
                        return "\n".join(text_parts)

                    return json.dumps(
                        result.structuredContent or {},
                        ensure_ascii=False,
                        default=str,
                    )

    except Exception as exc:
        import traceback

        traceback.print_exception(
            type(exc),
            exc,
            exc.__traceback__,
            limit=5,
        )

        cause = exc

        while cause.__cause__ or cause.__context__:
            cause = cause.__cause__ or cause.__context__

        print(
            "ROOT ERROR:",
            type(cause).__name__,
            str(cause)[:1000],
        )

        return "Movie recommendation service unavailable."
