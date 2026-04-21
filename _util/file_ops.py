"""
_util/file_ops.py
-----------------
Helpers for persisting node outputs to _temp/.
Every node must call save_json() before returning.
"""

import json
import os
from datetime import datetime
from pathlib import Path

TEMP_DIR = Path("_temp")
TEMP_DIR.mkdir(exist_ok=True)


def save_json(data: dict, prefix: str) -> str:
    """
    Write data to _temp/<prefix>_<timestamp>.json.
    Returns the file path so it can be logged.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = TEMP_DIR / f"{prefix}_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return str(filename)


def load_latest_json(prefix: str) -> dict:
    """Load the most recently written file matching prefix."""
    matches = sorted(TEMP_DIR.glob(f"{prefix}_*.json"), reverse=True)
    if not matches:
        raise FileNotFoundError(f"No _temp file with prefix '{prefix}'")
    with open(matches[0], encoding="utf-8") as f:
        return json.load(f)
