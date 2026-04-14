from __future__ import annotations

import asyncio

from backend.database import close_database, init_database


async def main() -> None:
    await init_database()
    await close_database()
    print("database initialized")


if __name__ == "__main__":
    asyncio.run(main())
