"""Database Seeding Script CLI for CSSS 441 Book Catalog."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.seed_service import seed_database

if __name__ == "__main__":
    count = seed_database()
    print(f"[SEED] Successfully seeded {count} new books into the catalog.")
