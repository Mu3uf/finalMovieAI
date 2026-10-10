import os
import json
import asyncio
import httpx

from contextvars import ContextVar
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from langchain_core.tools import tool

from app.services.mcp_warmup import wait_until_awake, mark_ok

load_dotenv()

CURRENT_USER_ID = ContextVar("CURRENT_USER_ID", default=None)

MCP_SERVER_URL = os.environ["MCP_SERVER_URL"]

# Cloudflare cuts requests at ~100s, so keep the total below that.
WAKE_WAIT_SECONDS = 70.0
RETRY_DEADLINE_SECONDS = 20.0
RETRY_STATUS = {502, 503, 504}

UNAVAILABLE_MESSAGE = (
    "The recommendation server is starting up. "
    "Please ask again in about a minute."
)


def _leaf_errors(exc: BaseException):
    if isinstance(exc, BaseExceptionGroup):
        for sub in exc.exceptions:
            yield from _leaf_errors(sub)
    else:
        yield exc


def _is_transient(exc: BaseException) -> bool:
    for leaf in _leaf_errors(exc):
        if (
            isinstance(leaf, httpx.HTTPStatusError)
            and leaf.response.status_code in RETRY_STATUS
        ):
            return True
        if isinstance(
            leaf,
            (
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
                httpx.RemoteProtocolError,
            ),
        ):
            return True
    return False


async def _with_retry(fn, deadline: float, first_delay: float = 2.0,
                      max_delay: float = 8.0):
    loop = asyncio.get_running_loop()
    end = loop.time() + deadline
    delay = first_delay
    attempt = 0

    while True:
        attempt += 1
        try:
            return await fn()
        except BaseException as exc:
            if isinstance(
                exc,
                (KeyboardInterrupt, SystemExit, asyncio.CancelledError),
            ):
                raise
            if not _is_transient(exc) or loop.time() + delay > end:
                raise
            print(f"[MCP RETRY] attempt {attempt}, retrying in {delay:.0f}s")
            await asyncio.sleep(delay)
            delay = min(delay * 2, max_delay)


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

    async def _call() -> str:
        timeout = httpx.Timeout(30.0, connect=30.0)

        async with httpx.AsyncClient(timeout=timeout) as http_client:
            async with streamable_http_client(
                MCP_SERVER_URL,
                http_client=http_client,
            ) as (read_stream, write_stream, _):

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
                    properties = remote_tool.inputSchema.get("properties", {})

                    accepted_arguments = {
                        key: value
                        for key, value in arguments.items()
                        if key in properties
                    }

                    result = await session.call_tool(
                        "recommend_unwatched_movies",
                        arguments=accepted_arguments,
                    )

                    mark_ok()

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

    try:
        # Usually already awake thanks to the startup/keep-warm task.
        if not await wait_until_awake(timeout=WAKE_WAIT_SECONDS):
            print("[MCP TOOL] server did not wake up in time")
            return UNAVAILABLE_MESSAGE

        return await _with_retry(_call, deadline=RETRY_DEADLINE_SECONDS)

    except BaseException as exc:
        import traceback

        if isinstance(
            exc,
            (KeyboardInterrupt, SystemExit, asyncio.CancelledError),
        ):
            raise

        print("=== MCP TOOL ERROR ===")
        print("MCP URL USED:", MCP_SERVER_URL)
        traceback.print_exception(
            type(exc),
            exc,
            exc.__traceback__,
            limit=5,
        )

        for leaf in _leaf_errors(exc):
            print("LEAF ERROR:", type(leaf).__name__, str(leaf)[:1000])

        return UNAVAILABLE_MESSAGE