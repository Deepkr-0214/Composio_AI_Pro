#!/usr/bin/env python3
"""
Dataset validation script for the Composio research agent.

Validates that:
1. apps.json exists and is valid JSON.
2. Contains exactly 100 unique applications.
3. Contains exactly 10 categories.
4. Every application has a valid category_id.
5. Every application has a unique id.
6. Every application has a non-empty name.
7. Each category has exactly 10 applications.
8. IDs are sequential from 1 to 100.
"""

import json
import sys
from pathlib import Path
from collections import Counter

DATA_DIR = Path(__file__).parent.parent / "data"
APPS_FILE = DATA_DIR / "apps.json"


def validate() -> bool:
    errors: list[str] = []
    warnings: list[str] = []

    # --- Check file exists ---
    if not APPS_FILE.exists():
        print(f"FAIL: {APPS_FILE} does not exist.")
        return False

    # --- Parse JSON ---
    try:
        with open(APPS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON — {e}")
        return False

    print(f"OK: {APPS_FILE} is valid JSON.")

    # --- Validate metadata ---
    metadata = data.get("metadata", {})
    if not metadata:
        warnings.append("No metadata section found.")

    # --- Validate categories ---
    categories = data.get("categories", [])
    category_ids = {c["id"] for c in categories}

    if len(categories) != 10:
        errors.append(f"Expected 10 categories, found {len(categories)}.")
    else:
        print(f"OK: Found exactly 10 categories.")

    if len(category_ids) != len(categories):
        errors.append("Duplicate category IDs detected.")

    # --- Validate applications ---
    apps = data.get("applications", [])

    # Total count
    if len(apps) != 100:
        errors.append(f"Expected 100 applications, found {len(apps)}.")
    else:
        print(f"OK: Found exactly 100 applications.")

    # Unique IDs
    app_ids = [a["id"] for a in apps]
    if len(set(app_ids)) != len(apps):
        dupes = [id_ for id_, count in Counter(app_ids).items() if count > 1]
        errors.append(f"Duplicate application IDs: {dupes}")
    else:
        print(f"OK: All application IDs are unique.")

    # Sequential IDs 1–100
    expected_ids = set(range(1, 101))
    actual_ids = set(app_ids)
    if actual_ids != expected_ids:
        missing = expected_ids - actual_ids
        extra = actual_ids - expected_ids
        if missing:
            errors.append(f"Missing IDs: {sorted(missing)}")
        if extra:
            errors.append(f"Unexpected IDs: {sorted(extra)}")
    else:
        print(f"OK: IDs are sequential from 1 to 100.")

    # Unique names
    app_names = [a["name"] for a in apps]
    if len(set(app_names)) != len(app_names):
        dupes = [n for n, count in Counter(app_names).items() if count > 1]
        errors.append(f"Duplicate application names: {dupes}")
    else:
        print(f"OK: All application names are unique.")

    # Non-empty names
    empty_names = [a["id"] for a in apps if not a.get("name", "").strip()]
    if empty_names:
        errors.append(f"Applications with empty names: {empty_names}")
    else:
        print(f"OK: All applications have non-empty names.")

    # Valid category references
    invalid_cats = [a for a in apps if a["category_id"] not in category_ids]
    if invalid_cats:
        errors.append(
            f"Apps with invalid category_id: "
            f"{[(a['id'], a['category_id']) for a in invalid_cats]}"
        )
    else:
        print(f"OK: All applications reference valid categories.")

    # 10 apps per category
    cat_counts = Counter(a["category_id"] for a in apps)
    unbalanced = {cid: cnt for cid, cnt in cat_counts.items() if cnt != 10}
    if unbalanced:
        cat_names = {c["id"]: c["name"] for c in categories}
        for cid, cnt in unbalanced.items():
            errors.append(
                f"Category '{cat_names.get(cid, cid)}' has {cnt} apps (expected 10)."
            )
    else:
        print(f"OK: Each category has exactly 10 applications.")

    # --- Summary ---
    print()
    if warnings:
        for w in warnings:
            print(f"WARNING: {w}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(f"\nVALIDATION FAILED — {len(errors)} error(s).")
        return False
    else:
        print("ALL VALIDATIONS PASSED ✓")
        return True


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)

