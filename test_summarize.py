"""
Root entry point for summarize test.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in (str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.test_summarize import run_summarize_tests
except ImportError:
    from test_summarize import run_summarize_tests  # type: ignore

if __name__ == "__main__":
    run_summarize_tests()
