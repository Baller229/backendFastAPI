# create_db.py
import os
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from models import Base
from dbhandler import _ensure_asyncpg, DATABASE_URL

async def main():
    dsn = _ensure_asyncpg(os.getenv("DATABASE_URL", DATABASE_URL))
    recreate = "--recreate" in sys.argv
    engine = create_async_engine(dsn)

    async with engine.begin() as conn:
        if recreate:
            print("DROP ALL (measurements)...")
            await conn.run_sync(Base.metadata.drop_all)
        print("CREATE ALL (ak netreba, nič sa nestane)...")
        await conn.run_sync(Base.metadata.create_all)
        print("TRUNCATE measurements...")
        await conn.execute(text("TRUNCATE TABLE measurements"))
    await engine.dispose()
    print("Hotovo. Tabuľka measurements existuje a je prázdna.")

if __name__ == "__main__":
    asyncio.run(main())
