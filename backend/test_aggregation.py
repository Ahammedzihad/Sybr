"""
Test script to verify frequently_reported_issues() against existing and edge-case database records.
"""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import storage
from aggregation import frequently_reported_issues


def main():
    print("==================================================")
    print("Testing frequently_reported_issues() on current DB")
    print("==================================================")

    initial_records = storage.get_all()
    print(f"Loaded {len(initial_records)} existing records from database.")

    # 1. Run on existing database records
    initial_summary = frequently_reported_issues()
    print("\n--- Current Aggregation Results ---")
    print("Categories:", initial_summary["by_category"])
    print("Top Keywords:", initial_summary["by_keyword"])

    # Basic validations on current records
    for cat, _ in initial_summary["by_category"]:
        assert cat.lower() != "unknown", f"Error: 'Unknown' category should be excluded, found '{cat}'"

    # 2. Inject edge case & malformed records to test resilience
    print("\n--- Injecting Edge-Case & Malformed Records ---")
    edge_cases = [
        # Normal category and keywords
        {
            "conversation_id": "TEST-AGG-01",
            "category": "Billing",
            "keywords": ["refund", "double_charge", "invoice"],
        },
        # Another billing to test count increment
        {
            "conversation_id": "TEST-AGG-02",
            "category": "Billing",
            "keywords": ["refund", "overdue"],
        },
        # Category is explicitly "Unknown" (must be ignored)
        {
            "conversation_id": "TEST-AGG-UNKNOWN",
            "category": "Unknown",
            "keywords": ["ignored_keyword_unknown"],
        },
        # Category is lowercase "unknown" (must be ignored)
        {
            "conversation_id": "TEST-AGG-UNKNOWN-LOWER",
            "category": "unknown",
            "keywords": ["test"],
        },
        # Category is None and keywords is None
        {
            "conversation_id": "TEST-AGG-NONE",
            "category": None,
            "keywords": None,
        },
        # Category is empty string and keywords is empty list
        {
            "conversation_id": "TEST-AGG-EMPTY",
            "category": "",
            "keywords": [],
        },
        # Malformed record with unexpected types
        {
            "conversation_id": "TEST-AGG-MALFORMED",
            "category": 12345,
            "keywords": "string_instead_of_list",
        },
        # Completely empty record dictionary
        {
            "conversation_id": "TEST-AGG-EMPTY-DICT",
        },
    ]

    for record in edge_cases:
        storage.save(record)
    print(f"Saved {len(edge_cases)} test records (including malformed/missing fields).")

    # 3. Re-run aggregation to verify count accuracy and lack of crashes
    updated_summary = frequently_reported_issues()
    print("\n--- Updated Aggregation Results ---")
    print("Categories:", updated_summary["by_category"])
    print("Top Keywords (max 10):", updated_summary["by_keyword"])

    category_dict = dict(updated_summary["by_category"])
    keyword_dict = dict(updated_summary["by_keyword"])

    # Assertions
    print("\n--- Validating Aggregation Logic ---")
    assert "Billing" in category_dict, "Billing should be present in by_category"
    assert category_dict["Billing"] >= 2, "Billing should have at least 2 counts"
    assert "Unknown" not in category_dict, "'Unknown' must be excluded"
    assert "unknown" not in category_dict, "'unknown' must be excluded"
    assert "" not in category_dict, "Empty category string must be excluded"
    assert None not in category_dict, "None category must be excluded"
    assert "refund" in keyword_dict, "'refund' keyword should be counted"
    assert len(updated_summary["by_keyword"]) <= 10, "by_keyword should contain at most 10 items"

    # 4. Test detect_resolution with multi-turn conversations and edge cases
    print("\n--- Testing detect_resolution() ---")
    from aggregation import detect_resolution
    from pipeline import run_pipeline

    # Test 1: Resolved pattern
    conv_resolved = [
        "Customer: I was charged twice for order #404.",
        "Agent: We verified the duplicate transaction and have refunded $25 to your card.",
        "Customer: Thank you, I see it confirmed on my banking app! Issue closed."
    ]
    res_1 = detect_resolution(conv_resolved)
    print("Conversation 1 (Resolved):", res_1)
    assert res_1 == "Resolved", f"Expected 'Resolved', got '{res_1}'"

    # Test 2: Unresolved pattern (agent says fixed, but customer signal still blocked)
    conv_unresolved = [
        "Customer: Unable to access the VPN server.",
        "Agent: The credentials have been fixed and your access is restored.",
        "Customer: I still haven't been able to log in and I'm still waiting."
    ]
    res_2 = detect_resolution(conv_unresolved)
    print("Conversation 2 (Unresolved):", res_2)
    assert res_2 == "Unresolved", f"Expected 'Unresolved', got '{res_2}'"

    # Test 3: Unresolved with 'no response' / 'again'
    conv_unresolved_2 = [
        "Customer: Please unlock my account.",
        "Customer: There is no response, my account failed again."
    ]
    res_3 = detect_resolution(conv_unresolved_2)
    print("Conversation 3 (Unresolved):", res_3)
    assert res_3 == "Unresolved", f"Expected 'Unresolved', got '{res_3}'"

    # Test 4: Pending pattern (normal ongoing conversation)
    conv_pending = [
        "Customer: Can you send me the tracking ID?",
        "Agent: We are contacting the carrier to retrieve the tracking link."
    ]
    res_4 = detect_resolution(conv_pending)
    print("Conversation 4 (Pending):", res_4)
    assert res_4 == "Pending", f"Expected 'Pending', got '{res_4}'"

    # Edge Case: Empty messages list
    res_empty = detect_resolution([])
    print("Conversation 5 (Empty list edge case):", res_empty)
    assert res_empty == "Unknown", f"Expected 'Unknown', got '{res_empty}'"

    # 5. Verify pipeline.py integration with multi-turn messages
    print("\n--- Validating pipeline.py run_pipeline integration ---")
    p_rec_resolved = run_pipeline("TEST-PIPE-RES", [{"text": m} for m in conv_resolved])
    print("Pipeline Resolved record resolution_status:", p_rec_resolved["resolution_status"])
    assert p_rec_resolved["resolution_status"] == "Resolved"

    p_rec_unresolved = run_pipeline("TEST-PIPE-UNRES", [{"text": m} for m in conv_unresolved])
    print("Pipeline Unresolved record resolution_status:", p_rec_unresolved["resolution_status"])
    assert p_rec_unresolved["resolution_status"] == "Unresolved"

    p_rec_pending = run_pipeline("TEST-PIPE-PEND", [{"text": m} for m in conv_pending])
    print("Pipeline Pending record resolution_status:", p_rec_pending["resolution_status"])
    assert p_rec_pending["resolution_status"] == "Pending"

    p_rec_empty = run_pipeline("TEST-PIPE-EMPTY", [])
    print("Pipeline Empty list record resolution_status:", p_rec_empty["resolution_status"])
    assert p_rec_empty["resolution_status"] == "Unknown"
    assert p_rec_empty.get("error") is None

    print("\nAll detect_resolution and pipeline wiring tests passed successfully!")
    print("==================================================")


def test_aggregation():
    import tempfile
    fresh_db = tempfile.NamedTemporaryFile(suffix="_agg_test.db", delete=False).name
    old_db = os.environ.get("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = fresh_db
    storage.init_db(fresh_db)
    try:
        main()
    finally:
        if old_db:
            os.environ["DATABASE_PATH"] = old_db
        else:
            os.environ.pop("DATABASE_PATH", None)
        if Path(fresh_db).exists():
            try:
                os.unlink(fresh_db)
            except OSError:
                pass


if __name__ == "__main__":
    main()
