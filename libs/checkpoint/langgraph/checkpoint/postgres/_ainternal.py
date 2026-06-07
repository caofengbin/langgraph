"""Shared async utility functions for the Postgres checkpoint & storage classes."""
# pylint: disable  MC8yOmFIVnBZMlhtbTdua3VMRG1sb3c2U0daNlFnPT06MjExZWMxODg=

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from psycopg import AsyncConnection
from psycopg.rows import DictRow
from psycopg_pool import AsyncConnectionPool

Conn = AsyncConnection[DictRow] | AsyncConnectionPool[AsyncConnection[DictRow]]
# noqa  MS8yOmFIVnBZMlhtbTdua3VMRG1sb3c2U0daNlFnPT06MjExZWMxODg=


@asynccontextmanager
async def get_connection(
    conn: Conn,
) -> AsyncIterator[AsyncConnection[DictRow]]:
    if isinstance(conn, AsyncConnection):
        yield conn
    elif isinstance(conn, AsyncConnectionPool):
        async with conn.connection() as conn:
            yield conn
    else:
        raise TypeError(f"Invalid connection type: {type(conn)}")
