"""
Offline Demo Cache Generator & Seeder.
Exports conversations and precomputed dashboard aggregates from the local SQLite/Supabase database
into `frontend/public/demo-cache.json` (and `frontend/dist/demo-cache.json`), enabling 100% offline
interactive presentation mode without requiring an active backend or live API connection.

Usage:
    python backend/scripts/seed_local.py
    python backend/scripts/seed_local.py --reload
"""
import sys
import os
import json
import argparse

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import get_all_conversations
from app.aggregates import compute_dashboard_data
from app.ingest import parse_csv_content, parse_json_content
from app.pipeline import process_conversation

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
SYNTH_PATH = os.path.join(DATA_DIR, "synthetic_phishing.json")
REAL_PATH = os.path.join(DATA_DIR, "sample_real.csv")

FRONTEND_PUBLIC = os.path.join(ROOT_DIR, "frontend", "public", "demo-cache.json")
FRONTEND_DIST = os.path.join(ROOT_DIR, "frontend", "dist", "demo-cache.json")


def populate_db_if_needed(force_reload: bool = False):
    existing = get_all_conversations()
    count = len(existing)
    if count > 0 and not force_reload:
        print(f"Database already contains {count} conversations.")
        return

    print("Populating database with synthetic and real datasets...")
    if os.path.exists(SYNTH_PATH):
        with open(SYNTH_PATH, "r", encoding="utf-8") as f:
            synth_raw = json.load(f)
        conversations_synth = parse_json_content(synth_raw)
        print(f"  Ingesting {len(conversations_synth)} synthetic phishing scenarios...")
        for conv in conversations_synth:
            process_conversation(conv, persist=True)
        print("  ✓ Synthetic phishing dataset seeded.")

    if os.path.exists(REAL_PATH):
        with open(REAL_PATH, "r", encoding="utf-8") as f:
            real_csv_str = f.read()
        conversations_real = parse_csv_content(real_csv_str)
        print(f"  Ingesting {len(conversations_real)} real customer support threads...")
        for conv in conversations_real:
            process_conversation(conv, persist=True)
        print("  ✓ Real customer support threads seeded.")


def generate_demo_cache():
    parser = argparse.ArgumentParser(description="Generate demo-cache.json for frontend offline mode.")
    parser.add_argument("--reload", action="store_true", help="Force reload datasets into the database before exporting.")
    args = parser.parse_args()

    print("=" * 65)
    print("  GENERATING FRONTEND OFFLINE DEMO CACHE")
    print("=" * 65)

    populate_db_if_needed(force_reload=args.reload)

    # 1. Fetch all conversations
    convs = get_all_conversations()
    print(f"\nFetched {len(convs)} analyzed conversations from database.")

    # 2. Compute dashboard aggregations
    dashboard = compute_dashboard_data()
    print("Computed real-time dashboard aggregations and KPIs.")

    # 3. Assemble full demo-cache payload
    payload = {
        "kpis": dashboard.kpis.model_dump(),
        "sentiment_distribution": dashboard.sentiment_distribution,
        "category_distribution": dashboard.category_distribution,
        "issue_frequency": [item.model_dump() for item in dashboard.issue_frequency],
        "risk_distribution": dashboard.risk_distribution,
        "emotion_distribution": dashboard.emotion_distribution,
        "daily_trend": dashboard.daily_trend,
        "conversations": [c.model_dump() for c in convs]
    }

    # 4. Write to frontend/public/demo-cache.json
    os.makedirs(os.path.dirname(FRONTEND_PUBLIC), exist_ok=True)
    with open(FRONTEND_PUBLIC, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"  ✓ Exported to: {FRONTEND_PUBLIC} ({len(payload['conversations'])} records)")

    # 5. Write to frontend/dist/demo-cache.json if dist folder exists
    if os.path.exists(os.path.dirname(FRONTEND_DIST)):
        with open(FRONTEND_DIST, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"  ✓ Synchronized with: {FRONTEND_DIST}")

    print("\nOffline demo cache ready! The React frontend can now operate 100% offline.")
    print("=" * 65)


if __name__ == "__main__":
    generate_demo_cache()
