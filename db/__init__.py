from .db import ApprovalDB

from asyncio import run
import asyncio

__all__ = ["db"]
db = ApprovalDB()

loop = asyncio.get_event_loop()
loop.run_until_complete(db.create_table())