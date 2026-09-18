"""
Root entry point for combined_intelligence test.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

for p in (str(BACKEND_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.test_combined_intelligence import main
except ImportError:
    from test_combined_intelligence import main  # type: ignore

if __name__ == "__main__":
    main()
