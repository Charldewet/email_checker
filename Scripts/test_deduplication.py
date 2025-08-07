#!/usr/bin/env python3
"""
Test Deduplication Logic
========================

This script tests the deduplication logic to show which files are kept.
"""

import os
import sys
from pathlib import Path
import re

def keep_latest_versions(base_dir: str):
    """Within the classified PDF tree keep only the latest time-stamped file per (date, pharmacy, report_type)"""
    base = Path(base_dir)
    if not base.exists():
        return
    
    latest_map = {}
    print(f"🔍 Analyzing files in: {base_dir}")
    
    # Traverse date/pharmacy folders
    for pdf in base.rglob("*.pdf"):
        name = pdf.name
        # Expected pattern: <report_type>_<HHMM>_originalname.pdf
        m = re.match(r"([a-z_]+)_(\d{4})_.*", name)
        if not m:
            continue
        report_type, hhmm = m.group(1), m.group(2)
        # parent directories give date and pharmacy
        try:
            pharmacy = pdf.parent.name  # pharmacy folder
            date_str = pdf.parent.parent.name  # date folder
        except Exception:
            continue
        key = (date_str, pharmacy, report_type)
        if key not in latest_map or hhmm > latest_map[key]["time"]:
            latest_map[key] = {"time": hhmm, "path": pdf}
            print(f"  📌 Latest for {key}: {hhmm} -> {pdf.name}")
    
    print(f"\n🗑️  Files to be removed:")
    # Delete older files
    for pdf in base.rglob("*.pdf"):
        name = pdf.name
        m = re.match(r"([a-z_]+)_(\d{4})_.*", name)
        if not m:
            continue
        report_type, hhmm = m.group(1), m.group(2)
        pharmacy = pdf.parent.name
        date_str = pdf.parent.parent.name
        key = (date_str, pharmacy, report_type)
        if key in latest_map and latest_map[key]["path"] != pdf:
            print(f"  ❌ Remove: {pdf.name} (older than {latest_map[key]['time']})")
            # pdf.unlink(missing_ok=True)  # Commented out to just show what would be removed
    
    print(f"\n✅ Files to be kept:")
    for key, info in latest_map.items():
        print(f"  ✅ Keep: {info['path'].name} (time: {info['time']})")

if __name__ == "__main__":
    keep_latest_versions("temp_classified_test") 