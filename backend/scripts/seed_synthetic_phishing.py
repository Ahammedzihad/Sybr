"""
Dataset Seeder: Loads synthetic_phishing.json and sample_real.csv into the database.
Run: python backend/scripts/seed_synthetic_phishing.py
"""
import sys
import os
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ingest import parse_csv_content, parse_json_content
from app.pipeline import process_conversation
from app.db import get_all_conversations

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
SYNTH_PATH = os.path.join(DATA_DIR, "synthetic_phishing.json")
REAL_PATH = os.path.join(DATA_DIR, "sample_real.csv")


def seed_datasets():
    print("=" * 60)
    print("  SEEDING DATASETS INTO DATABASE")
    print("=" * 60)

    # 1. Seed synthetic phishing dataset
    if os.path.exists(SYNTH_PATH):
        with open(SYNTH_PATH, "r") as f:
            synth_raw = json.load(f)
        conversations_synth = parse_json_content(synth_raw)
        print(f"Ingesting {len(conversations_synth)} synthetic phishing scenarios...")
        for conv in conversations_synth:
            process_conversation(conv, persist=True)
        print("  ✓ Synthetic phishing dataset seeded successfully.")
    else:
        print(f"Warning: {SYNTH_PATH} not found.")

    # 2. Seed real customer tickets
    if os.path.exists(REAL_PATH):
        with open(REAL_PATH, "r") as f:
            real_csv_str = f.read()
        conversations_real = parse_csv_content(real_csv_str)
        print(f"Ingesting {len(conversations_real)} real customer support threads...")
        for conv in conversations_real:
            process_conversation(conv, persist=True)
        print("  ✓ Real customer support threads seeded successfully.")
    else:
        print(f"Warning: {REAL_PATH} not found.")

    # Summary
    all_convs = get_all_conversations()
    print(f"\nTotal conversations now in database: {len(all_convs)}")
    print("=" * 60)


if __name__ == "__main__":
    seed_datasets()
