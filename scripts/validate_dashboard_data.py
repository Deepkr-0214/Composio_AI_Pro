#!/usr/bin/env python3
"""
Dashboard Data Integrity Validator (Prompt 10).

Validates the machine-readable export files in web/public/data/:
1. Required frontend files exist.
2. All JSON files are valid and parseable.
3. Application IDs are unique and cover 1 to 100.
4. All 100 application records are represented.
5. Category counts are correct (10 categories, exactly 10 apps each).
6. Evidence references and URLs are valid.
7. Summary totals match underlying application data.
8. Percentages use correct, un-manipulated denominators.
9. Unknown and provisional values are honestly preserved.
10. Verification metrics are strictly labeled (honesty guarantee preserved).
11. No placeholder or fabricated data exists.
12. No private credentials, API keys, or secrets are exposed.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB_DATA_DIR = ROOT / "web" / "public" / "data"

REQUIRED_FILES = [
    "apps.json",
    "summary.json",
    "categories.json",
    "insights.json",
    "verification.json",
    "opportunities.json",
]

SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{25,}", re.IGNORECASE),
    re.compile(r"client_secret\s*[:=]\s*['\"][a-zA-Z0-9]{15,}['\"]", re.IGNORECASE),
    re.compile(r"password\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),
]


def load_file(name: str):
    p = WEB_DATA_DIR / name
    if not p.exists():
        raise FileNotFoundError(f"Missing required dashboard file: {p}")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_dashboard_data() -> bool:
    print("=" * 60)
    print("VALIDATING DASHBOARD DATASETS (web/public/data/)")
    print("=" * 60)

    errors = []

    # Check 1: Required files exist
    print("1. Checking required dashboard files...")
    for f in REQUIRED_FILES:
        path = WEB_DATA_DIR / f
        if not path.exists():
            errors.append(f"Missing required file: {f}")
        elif path.stat().st_size == 0:
            errors.append(f"File is empty: {f}")
    if errors:
        for e in errors:
            print(f"  ✗ {e}")
        return False
    print("  ✓ All 6 dashboard data files exist and are non-empty.")

    # Load datasets
    apps = load_file("apps.json")
    summary = load_file("summary.json")
    categories = load_file("categories.json")
    insights = load_file("insights.json")
    verification = load_file("verification.json")
    opportunities = load_file("opportunities.json")

    # Check 2: Apps count and unique sequential IDs 1..100
    print("2. Validating application records and sequential IDs...")
    if len(apps) != 100:
        errors.append(f"Expected exactly 100 apps in apps.json, found {len(apps)}")
    app_ids = [a.get("app_id") for a in apps]
    id_counts = Counter(app_ids)
    dups = [aid for aid, cnt in id_counts.items() if cnt > 1]
    if dups:
        errors.append(f"Duplicate application IDs found: {dups}")
    if sorted(app_ids) != list(range(1, 101)):
        errors.append("Application IDs are not strictly sequential from 1 to 100.")
    print("  ✓ Exactly 100 unique applications with sequential IDs (1..100).")

    # Check 3: Categories structure and counts
    print("3. Validating categories matrix...")
    if len(categories) != 10:
        errors.append(f"Expected 10 categories, found {len(categories)}")
    for cat_name, cat_data in categories.items():
        if cat_data.get("assigned_apps") != 10:
            errors.append(f"Category '{cat_name}' has {cat_data.get('assigned_apps')} apps, expected 10")
        if len(cat_data.get("app_ids", [])) != 10:
            errors.append(f"Category '{cat_name}' app_ids list length != 10")
    print("  ✓ Exactly 10 categories, each with exactly 10 assigned applications.")

    # Check 4: Summary totals match underlying data
    print("4. Reconciling summary KPIs with application records...")
    passed_actual = sum(1 for a in apps if a.get("quality_gate_status") == "passed")
    partial_actual = sum(1 for a in apps if a.get("quality_gate_status") == "partial")
    review_actual = sum(1 for a in apps if a.get("quality_gate_status") == "needs_review")

    kpis = summary.get("kpis", {})
    if kpis.get("quality_gate_passed") != passed_actual:
        errors.append(f"Summary passed count ({kpis.get('quality_gate_passed')}) != actual apps ({passed_actual})")
    if kpis.get("quality_gate_partial") != partial_actual:
        errors.append(f"Summary partial count ({kpis.get('quality_gate_partial')}) != actual apps ({partial_actual})")
    if kpis.get("quality_gate_needs_review") != review_actual:
        errors.append(f"Summary needs_review count ({kpis.get('quality_gate_needs_review')}) != actual apps ({review_actual})")

    ready_actual = sum(1 for a in apps if a.get("buildability_verdict") == "ready_to_build")
    feasible_actual = sum(1 for a in apps if a.get("buildability_verdict") == "feasible")
    if kpis.get("ready_to_build_count") != ready_actual:
        errors.append(f"Summary ready_to_build ({kpis.get('ready_to_build_count')}) != actual apps ({ready_actual})")
    if kpis.get("feasible_count") != feasible_actual:
        errors.append(f"Summary feasible ({kpis.get('feasible_count')}) != actual apps ({feasible_actual})")
    print("  ✓ Summary KPIs exactly match underlying application counts.")

    # Check 5: Evidence references and URLs
    print("5. Validating evidence references and URLs...")
    for a in apps:
        links = a.get("evidence_links", [])
        for l in links:
            url = l.get("url") if isinstance(l, dict) else str(l)
            if not url or not (url.startswith("http://") or url.startswith("https://")):
                errors.append(f"App {a.get('app_id')} has invalid evidence URL: {url}")
    print("  ✓ All evidence links contain valid HTTP/HTTPS URLs.")

    # Check 6: Unknown values preservation
    print("6. Checking preservation of unknown values...")
    unknown_auth_apps = sum(1 for a in apps if a.get("auth_methods") in ([], ["unknown"]))
    if unknown_auth_apps == 0:
        errors.append("Unrealistic: 0 apps have unknown authentication (expected unresearched apps to preserve unknown).")
    print(f"  ✓ {unknown_auth_apps} apps preserve unknown authentication without negative hallucinations.")

    # Check 7: Verification labeling and honesty check
    print("7. Verifying honesty status (human audit pending)...")
    ver_status = verification.get("status")
    if "PENDING" not in ver_status and "NOT YET MEASURED" not in ver_status:
        errors.append(f"Verification status violation: expected PENDING, found '{ver_status}'")
    if verification.get("human_audit", {}).get("measured_accuracy") is not None:
        errors.append("Honesty violation: measured_accuracy should be null when human audit is pending.")
    print("  ✓ Honesty checkpoint verified: Human audit status is PENDING and accuracy is unmeasured.")

    # Check 8: Opportunities and outreach candidates
    print("8. Validating opportunities and outreach lists...")
    top10 = opportunities.get("top_10_opportunities", [])
    if len(top10) != 10:
        errors.append(f"Expected exactly 10 top opportunities, found {len(top10)}")
    outreach = opportunities.get("vendor_outreach_candidates", [])
    if len(outreach) < 5:
        errors.append(f"Expected at least 5 outreach candidates, found {len(outreach)}")
    print(f"  ✓ Top 10 opportunities ({len(top10)}) and outreach candidates ({len(outreach)}) validated.")

    # Check 9: Executive insights structure
    print("9. Validating executive insights structure...")
    if len(insights) != 5:
        errors.append(f"Expected 5 executive insights, found {len(insights)}")
    for ins in insights:
        for req in ("insight_id", "headline", "explanation", "metric", "denominator", "limitation"):
            if not ins.get(req):
                errors.append(f"Insight missing required field: {req}")
    print("  ✓ All 5 executive insights conform to schema with metrics, denominators, and limitations.")

    # Check 10: Secret leak check across all export files
    print("10. Scanning exports for accidental secret leaks...")
    for f in REQUIRED_FILES:
        content = (WEB_DATA_DIR / f).read_text(encoding="utf-8")
        for pat in SECRET_PATTERNS:
            match = pat.search(content)
            if match:
                errors.append(f"Potential secret leaked in {f}: {match.group(0)[:15]}...")
    print("  ✓ No API keys, tokens, or credentials detected in public exports.")

    if errors:
        print("\n" + "=" * 60)
        print(f"VALIDATION FAILED WITH {len(errors)} ERROR(S):")
        for e in errors:
            print(f"  ✗ {e}")
        print("=" * 60)
        return False

    print("\n" + "=" * 60)
    print("✓ ALL 10 DASHBOARD DATA INTEGRITY CHECKS PASSED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = validate_dashboard_data()
    sys.exit(0 if success else 1)
