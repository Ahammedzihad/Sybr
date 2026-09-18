"""
Test script to validate keyword extraction on real customer conversation datasets.
Root entry point.
"""

import sys
from pathlib import Path

# Ensure backend and root directories are in sys.path
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in (str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.test_keywords import (
        load_dataset,
        main,
        print_summary,
        run_keyword_analysis,
        save_handoff_results,
    )
except ImportError:
    from test_keywords import (  # type: ignore
        load_dataset,
        main,
        print_summary,
        run_keyword_analysis,
        save_handoff_results,
    )

if __name__ == "__main__":
    main()
