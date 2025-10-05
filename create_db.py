# create_db.py
import os
import asyncio
import argparse
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from models import Base
from dbhandler import _ensure_asyncpg, DATABASE_URL


async def main():
    parser = argparse.ArgumentParser(description="Init DB schema")
    parser.add_argument("--recreate", action="store_true",
                        help="Drop and recreate all tables (DESTRUCTIVE).")
    parser.add_argument("--truncate", action="store_true",
                        help="TRUNCATE TABLE measurements after ensuring schema.")
    args = parser.parse_args()

    dsn = _ensure_asyncpg(os.getenv("DATABASE_URL", DATABASE_URL))
    engine = create_async_engine(dsn)

    async with engine.begin() as conn:
        if args.recreate:
            print("DROP ALL (entire metadata)…")
            await conn.run_sync(Base.metadata.drop_all)
            print("CREATE ALL…")
            await conn.run_sync(Base.metadata.create_all)
        else:

            print("CREATE ALL (idempotent; existing data preserved)…")
            await conn.run_sync(Base.metadata.create_all)

        if args.truncate:
            print("TRUNCATE measurements…")
            await conn.execute(text("TRUNCATE TABLE measurements"))

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
