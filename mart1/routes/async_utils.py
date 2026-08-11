"""Helpers for running sync route logic without blocking the event loop."""

import asyncio
from functools import wraps


def async_route(func):
    """Run a synchronous route handler in a worker thread."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper