import asyncpg
from contextlib import asynccontextmanager
from app.configs.settings import settings

_connection_pool: asyncpg.Pool | None = None


async def init_db_pool():
    """Initialize the database connection pool."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = await asyncpg.create_pool(
            user=settings.db_user,
            password=settings.db_pass,
            database=settings.db_name,
            host=settings.db_host,
            port=settings.db_port,
            min_size=1,
            max_size=5,
            max_inactive_connection_lifetime=300,
        )
    return _connection_pool


def get_db_pool() -> asyncpg.Pool:
    """Get the initialized database connection pool."""
    if _connection_pool is None:
        raise RuntimeError("DB pool not initialized. Call init_db_pool() first.")
    return _connection_pool


@asynccontextmanager
async def get_db_connection():
    """Dùng connection trong async with, tự release sau khi dùng"""
    if _connection_pool is None:
        raise RuntimeError("Database pool chưa được init. Gọi init_db_pool() trước.")
    conn = await _connection_pool.acquire()
    try:
        yield conn
    finally:
        await _connection_pool.release(conn)


async def close_db_pool():
    """Đóng pool khi app shutdown"""
    global _connection_pool
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None


async def cleanup_idle_connections(pool):
    """Terminate idle connections to free slots."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT pid
            FROM pg_stat_activity
            WHERE state = 'idle' AND usename = $1
        """,
            settings.db_user,
        )

        for row in rows:
            await conn.execute(f"SELECT pg_terminate_backend({row['pid']})")
