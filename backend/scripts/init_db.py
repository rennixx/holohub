"""Initialize database tables."""
import asyncio
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import init_db


async def main():
    """Initialize database."""
    print("Creating database tables...")
    await init_db()
    print("Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(main())
