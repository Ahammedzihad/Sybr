"""
Phase 2 Database Verification Script
Tests CRUD operations against Supabase Postgres:
1. Connect
2. Insert test record
3. Retrieve record
4. Update record
5. Confirm updated value
6. Clean up test record
"""
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from app.config import settings
from app.db import (
    get_supabase_client,
    is_supabase_enabled,
    upsert_conversation,
    get_conversation,
    delete_conversation,
)
from app.schemas import (
    ConversationRecord,
    SummaryDetail,
    SecurityDetail,
    Message,
)


def run_test():
    print("=" * 60)
    print("  SUPABASE DATABASE VERIFICATION TEST")
    print("=" * 60)
    print(f"Supabase URL: {settings.SUPABASE_URL}")
    print(f"Supabase Key Set: {bool(settings.SUPABASE_SERVICE_ROLE_KEY)}")

    if not is_supabase_enabled():
        print("ERROR: Supabase credentials are not set in backend/.env!")
        return False

    client = get_supabase_client()
    if not client:
        print("ERROR: Failed to create Supabase client.")
        return False
    print("[1/6] Supabase client initialized successfully.")

    test_id = f"TEST-DEPLOY-{int(datetime.now().timestamp())}"
    test_record = ConversationRecord(
        conversation_id=test_id,
        channel="email",
        created_at=datetime.now(timezone.utc).isoformat(),
        source="verification_test",
        raw_text_masked="Verification test customer ticket content.",
        category="Technical Problem",
        issue_label="App Crash/Bug",
        customer_issue="App crashes on login",
        sentiment="Negative",
        emotion="Frustration",
        emotion_intensity=3,
        is_angry=False,
        urgency="Medium",
        priority="Medium",
        priority_reason="User cannot access account",
        resolution_status="Pending",
        resolution_reason="Awaiting tech investigation",
        summary=SummaryDetail(
            issue="App crashes on login",
            customer_request="Fix login crash",
            actions_taken="Created test ticket",
            current_status="Pending",
            priority="Medium"
        ),
        security=SecurityDetail(
            threat_detected=False,
            threat_type="None",
            social_engineering="No",
            techniques=[],
            suspicious_url=False,
            suspicious_domain=False,
            suspicious_email=False,
            suspicious_attachment=False,
            credential_request=False,
            otp_request=False,
            rule_score=0,
            risk_level="Low",
            risk_reasons=["No indicators of attack"],
            recommended_action="Normal support handling"
        ),
        messages=[
            Message(sender="customer", text="App crashes on login", timestamp=datetime.now(timezone.utc).isoformat())
        ],
        ai_mode="fallback",
        processing_ms=10,
    )

    # 1. Insert test record
    print(f"\n[2/6] Inserting test record: {test_id}...")
    try:
        upsert_conversation(test_record)
        print("      Insert operation executed without error.")
    except Exception as e:
        print(f"ERROR inserting: {e}")
        return False

    # 2. Retrieve test record directly from Supabase
    print(f"\n[3/6] Retrieving record {test_id} from Supabase...")
    try:
        res = client.table("conversations").select("*").eq("id", test_id).execute()
        if not res.data:
            print(f"ERROR: Record {test_id} was not found in Supabase table 'conversations'.")
            return False
        retrieved = res.data[0]
        print(f"      Retrieved: id={retrieved.get('id')}, category={retrieved.get('category')}, priority={retrieved.get('priority')}")
    except Exception as e:
        print(f"ERROR querying Supabase: {e}")
        return False

    # 3. Update test record
    print(f"\n[4/6] Updating record {test_id} to Priority='Critical' and Status='Resolved'...")
    try:
        test_record.priority = "Critical"
        test_record.resolution_status = "Resolved"
        test_record.customer_issue = "App crashes on login - RESOLVED"
        upsert_conversation(test_record)
        print("      Update executed.")
    except Exception as e:
        print(f"ERROR updating: {e}")
        return False

    # 4. Confirm updated value
    print(f"\n[5/6] Confirming updated record from Supabase...")
    try:
        res2 = client.table("conversations").select("*").eq("id", test_id).execute()
        if not res2.data:
            print(f"ERROR: Record {test_id} not found after update.")
            return False
        updated_row = res2.data[0]
        assert updated_row.get("priority") == "Critical", f"Expected Critical, got {updated_row.get('priority')}"
        assert updated_row.get("resolution_status") == "Resolved", f"Expected Resolved, got {updated_row.get('resolution_status')}"
        print(f"      Confirmed update: priority={updated_row.get('priority')}, resolution_status={updated_row.get('resolution_status')}")
    except Exception as e:
        print(f"ERROR verifying update: {e}")
        return False

    # 5. Clean up test record
    print(f"\n[6/6] Cleaning up test record {test_id}...")
    try:
        delete_conversation(test_id)
        verify_del = client.table("conversations").select("id").eq("id", test_id).execute()
        if verify_del.data:
            print("WARNING: Test record was not deleted cleanly.")
        else:
            print("      Clean up confirmed! Record deleted.")
    except Exception as e:
        print(f"ERROR during cleanup: {e}")
        return False

    print("\n" + "=" * 60)
    print("  ALL 6 SUPABASE CRUD OPERATIONS PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
