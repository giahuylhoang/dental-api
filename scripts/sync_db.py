"""
Sync database: initialize schema and seed initial data.

Run this before starting the API locally or before deployment.
Database is the source of truth for appointments (no external calendar sync).
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database.connection import init_db
from scripts.init_database import seed_initial_data


def main():
    print("Syncing database (init + seed)...")
    print("=" * 50)
    init_db()
    print("✓ Database tables ready")
    seed_initial_data()
    print("=" * 50)
    print("✓ Database sync complete!")


if __name__ == "__main__":
    main()
