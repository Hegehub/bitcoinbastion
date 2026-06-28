from __future__ import annotations

import sys
from pathlib import Path

REFLEX_ROOT = Path(__file__).resolve().parents[1]
if str(REFLEX_ROOT) not in sys.path:
    sys.path.insert(0, str(REFLEX_ROOT))
