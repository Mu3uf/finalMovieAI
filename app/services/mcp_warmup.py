"""Keeps the Render-hosted MCP server awake while the main app is running."""

import asyncio
import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "")

# Contact newer than this counts as "awake" (no ping needed).
FRESH_SECONDS = 240.0
# Render free sleeps after ~15 min idle. Worst case gap between contacts is
# FRESH_SECONDS + KEEP_WARM_INTERVAL = 13.5 min, so it never reaches 15.
KEEP_WARM_INTERVAL = 540.0
WAKE_DEADLINE = 180.0
WAKE_DELAY = 5.0
TRANSIENT_STATUS = {502, 503, 504}

_last_ok: float | None = None
_wake_task: asyncio.Task | None = None
_keep_warm_task: asyncio.Task | None = None


def mark_ok() -> None:
    global _last_ok
    _last_ok = time.monotonic()


def is_fresh() -> bool:
    return _last_ok is not None and (time.monotonic() - _last_ok) < FRESH_SECONDS


async def _do_wake() -> bool:
    if not MCP_SERVER_URL:
        print("[MCP WARMUP] MCP_SERVER_URL is not set")
        return False

    loop = asyncio.get_running_loop()
    end = loop.time() + WAKE_DEADLINE
    attempt = 0

    async with httpx.AsyncClient(timeout=15.0) as client:
        while loop.time() < end:
            attempt += 1
            try:
                response = await client.get(MCP_SERVER_URL)
                # 400/405/406 are fine: the server answered, so it is awake.
                if response.status_code not in TRANSIENT_STATUS:
                    mark_ok()
                    print(f"[MCP WARMUP] awake after {attempt} attempt(s)")
                    return True
            except httpx.HTTPError:
                pass
            await asyncio.sleep(WAKE_DELAY)

    print("[MCP WARMUP] gave up waiting for the MCP server")
    return False


def _ensure_wake_task() -> asyncio.Task:
    """One shared wake-up task, no matter how many callers need it."""
    global _wake_task
    if _wake_task is None or _wake_task.done():
        _wake_task = asyncio.create_task(_do_wake())
    return _wake_task


async def wait_until_awake(timeout: float = 70.0) -> bool:
    """Wait (up to `timeout` seconds) until the MCP server answers."""
    if is_fresh():
        return True
    task = _ensure_wake_task()
    try:
        return await asyncio.wait_for(asyncio.shield(task), timeout)
    except asyncio.TimeoutError:
        return False


def warm_in_background() -> None:
    """Start waking the server without waiting for it."""
    if not is_fresh():
        _ensure_wake_task()


async def _keep_warm_loop() -> None:
    while True:
        try:
            await wait_until_awake(timeout=WAKE_DEADLINE + 10)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print("[MCP WARMUP] loop error:", repr(exc))
        await asyncio.sleep(KEEP_WARM_INTERVAL)


def start_keep_warm() -> None:
    global _keep_warm_task
    if _keep_warm_task is None or _keep_warm_task.done():
        _keep_warm_task = asyncio.create_task(_keep_warm_loop())


async def stop_keep_warm() -> None:
    global _keep_warm_task
    if _keep_warm_task is not None:
        _keep_warm_task.cancel()
        try:
            await _keep_warm_task
        except (asyncio.CancelledError, Exception):
            pass
        _keep_warm_task = None