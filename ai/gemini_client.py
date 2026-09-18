"""
Gemini AI client integration module (Root package entry).
Proxies/Imports functions from backend/ai/gemini_client.py or runs standalone.
"""

import sys
from pathlib import Path

# Add project root and backend directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in (str(ROOT_DIR), str(BACKEND_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.ai.gemini_client import (
        DEFAULT_MODEL,
        FALLBACK_MODEL,
        FALLBACK_MODELS,
        GEMINI_API_KEY,
        analyze,
        combined_intelligence,
        get_model,
        mask_pii,
        process_conversation,
        summarize,
        test_hello_world,
    )
except ImportError:
    from ai.gemini_client import (  # type: ignore
        DEFAULT_MODEL,
        FALLBACK_MODEL,
        FALLBACK_MODELS,
        GEMINI_API_KEY,
        analyze,
        combined_intelligence,
        get_model,
        mask_pii,
        process_conversation,
        summarize,
        test_hello_world,
    )

if __name__ == "__main__":
    test_hello_world()
