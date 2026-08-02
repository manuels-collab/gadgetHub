import asyncio
from flask import copy_current_request_context


async def run_blocking(func, *args, **kwargs):
    """Run a synchronous blocking operation in a worker thread while preserving Flask request context."""
    wrapped = copy_current_request_context(func)
    return await asyncio.to_thread(wrapped, *args, **kwargs)
