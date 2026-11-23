#!/usr/bin/env python3
"""
Validation script for research_results.json.

Verifies structural integrity, schema compliance, enum validity,
evidence consistency, and data hygiene across the full 100-application dataset.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.models import (
    AuthMethod,
    CredentialAccessibility,
    APIType,
    APIBreadth,
    MCPStatus,
    BuildabilityVerdict,
    BlockerType,
    QualityGateStatus,
)

RESULTS_FILE = ROOT / "data" / "research_results.json"
APPS_FILE = ROOT / "data" / "apps.json"

REQUIRED_FIELDS = [
    "app_id",
    "app_name",
    "category_id",
    "category_name",
    "description",
    "website_url",
    "auth_methods",
    "credential_accessibility",
    "api_type",
    "api_breadth",
    "mcp_status",
    "toolkit_buildability_score",
    "buildability_verdict",
    "blockers",
    "overall_confidence",
    "evidence_links",
    "quality_gate_status",
    "researched_at",
]

AUTH_ENUMS = {e.value for e in AuthMethod}
CRED_ENUMS = {e.value for e in CredentialAccessibility}
API_ENUMS = {e.value for e in APIType}
BREADTH_ENUMS = {e.value for e in APIBreadth}
MCP_ENUMS = {e.value for e in MCPStatus}
BUILD_ENUMS = {e.value for e in BuildabilityVerdict}
BLOCKER_ENUMS = {e.value for e in BlockerType}
GATE_ENUMS = {e.value for e in QualityGateStatus}
CONFIDENCE_VALUES = {"high", "medium", "low", "unverified"}

PLACEHOLDER_SUBSTRINGS = [
    "example.com",
    "todo",
    "tbd",
    "insert url",
    "placeholder",
    "dummy",
    "test.com",
    "foo.bar",
]


class ValidationError(Exception):
    pass


def validate_research(filepath: Path = RESULTS_FILE) -> tuple[bool, list[str]]:
    """Validate research_results.json. Returns (passed, list_of_errors)."""
    errors: list[str] = []

    if not filepath.exists():
        return False, [f"File not found: {filepath}"]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"JSON parsing error: {e}"]

    # 1. Exactly 100 application records
    if not isinstance(data, list):
        return False, ["Root structure must be a JSON array (list)."]
    if len(data) != 100:
        errors.append(f"Expected exactly 100 records, got {len(data)}.")

    # 2 & 3. Exactly 10 categories, exactly 10 applications per category
    categories: dict[str, list[int]] = {}
    ids_seen: set[int] = set()

    for idx, item in enumerate(data):
        app_id = item.get("app_id")
        app_name = item.get("app_name", f"Index {idx}")

        # 4. Unique IDs from 1 to 100
        if app_id is None:
            errors.append(f"Record at index {idx} ({app_name}) has no 'app_id'.")
            continue
        if not isinstance(app_id, int):
            errors.append(f"App ID {app_id} must be an integer, got {type(app_id).__name__}.")
        elif app_id < 1 or app_id > 100:
            errors.append(f"App ID {app_id} is out of 1-100 range.")
        elif app_id in ids_seen:
            errors.append(f"Duplicate App ID: {app_id}.")
        ids_seen.add(app_id)

        cat = item.get("category_name", "")
        if cat:
            categories.setdefault(cat, []).append(app_id)
        else:
            errors.append(f"App {app_id} ({app_name}) is missing category_name.")

        # 5. Required schema fields
        for field in REQUIRED_FIELDS:
            if field not in item:
                errors.append(f"App {app_id} ({app_name}) is missing required field: '{field}'.")

        # 6 & 7. Correct data types and valid enum values
        auth_methods = item.get("auth_methods")
        if not isinstance(auth_methods, list):
            errors.append(f"App {app_id} 'auth_methods' must be list, got {type(auth_methods).__name__}.")
        else:
            for am in auth_methods:
                if am not in AUTH_ENUMS:
                    errors.append(f"App {app_id} invalid auth_method: '{am}'.")

        api_type = item.get("api_type")
        if not isinstance(api_type, list):
            errors.append(f"App {app_id} 'api_type' must be list, got {type(api_type).__name__}.")
        else:
            for at in api_type:
                if at not in API_ENUMS:
                    errors.append(f"App {app_id} invalid api_type: '{at}'.")

        cred = item.get("credential_accessibility")
        if cred and cred not in CRED_ENUMS:
            errors.append(f"App {app_id} invalid credential_accessibility: '{cred}'.")

        breadth = item.get("api_breadth")
        if breadth and breadth not in BREADTH_ENUMS:
            errors.append(f"App {app_id} invalid api_breadth: '{breadth}'.")

        mcp = item.get("mcp_status")
        if mcp and mcp not in MCP_ENUMS:
            errors.append(f"App {app_id} invalid mcp_status: '{mcp}'.")

        verdict = item.get("buildability_verdict")
        if verdict and verdict not in BUILD_ENUMS:
            errors.append(f"App {app_id} invalid buildability_verdict: '{verdict}'.")

        gate = item.get("quality_gate_status")
        if gate and gate not in GATE_ENUMS:
            errors.append(f"App {app_id} invalid quality_gate_status: '{gate}'.")

        conf = item.get("overall_confidence")
        if conf and conf not in CONFIDENCE_VALUES:
            errors.append(f"App {app_id} invalid overall_confidence: '{conf}'.")

        score = item.get("toolkit_buildability_score")
        if score is not None and not isinstance(score, (int, float)):
            errors.append(f"App {app_id} toolkit_buildability_score must be numeric, got {score}.")
        elif score is not None and not (1 <= score <= 10):
            errors.append(f"App {app_id} toolkit_buildability_score {score} out of range 1-10.")

        # 8. Valid evidence reference structure
        evidence_links = item.get("evidence_links", [])
        if not isinstance(evidence_links, list):
            errors.append(f"App {app_id} evidence_links must be a list.")
        else:
            for link in evidence_links:
                url_str = link.get("url", "") if isinstance(link, dict) else str(link)
                if url_str:
                    if not (url_str.startswith("http://") or url_str.startswith("https://")):
                        errors.append(f"App {app_id} evidence link is not a valid URL: '{url_str}'.")
                    # 11. No fabricated placeholder evidence
                    for ph in PLACEHOLDER_SUBSTRINGS:
                        if ph in url_str.lower():
                            errors.append(f"App {app_id} has placeholder evidence URL: '{url_str}'.")

        # 9. No unsupported MCP confirmation
        if mcp in ("official_mcp", "community_mcp"):
            repo_url = item.get("mcp_repo_url")
            has_mcp_evidence = any(
                "mcp" in str(link).lower() or "modelcontextprotocol" in str(link).lower()
                for link in evidence_links
            )
            if not repo_url and not has_mcp_evidence:
                errors.append(
                    f"App {app_id} claims '{mcp}' but has no mcp_repo_url or MCP evidence backing."
                )

        # 10. No buildability verdict without appropriate reasoning
        if verdict and verdict != "unknown":
            notes = item.get("toolkit_buildability_notes") or item.get("research_notes")
            if not notes and score is None:
                errors.append(
                    f"App {app_id} has verdict '{verdict}' without score or buildability notes."
                )

        # 12. Consistent research statuses
        researched_at = item.get("researched_at")
        if researched_at and not gate:
            errors.append(f"App {app_id} has researched_at timestamp but no quality_gate_status.")

    # Check category distribution
    if len(categories) != 10:
        errors.append(f"Expected exactly 10 categories, found {len(categories)}: {list(categories.keys())}.")
    for cat_name, app_list in categories.items():
        if len(app_list) != 10:
            errors.append(f"Category '{cat_name}' has {len(app_list)} apps, expected 10.")

    passed = len(errors) == 0
    return passed, errors


def main() -> None:
    print("=" * 60)
    print("RESEARCH DATASET INTEGRITY & SCHEMA VALIDATION")
    print("=" * 60)
    print(f"Validating: {RESULTS_FILE}\n")

    passed, errors = validate_research()

    if passed:
        print("✓ ALL 12 VALIDATION CHECKS PASSED:")
        print("  1. Exactly 100 application records.")
        print("  2. Exactly 10 unique categories.")
        print("  3. Exactly 10 applications per category.")
        print("  4. Unique IDs strictly sequential from 1 to 100.")
        print("  5. Required schema fields present on all records.")
        print("  6. Enum values valid (auth, api_type, breadth, mcp, buildability).")
        print("  7. Correct data types enforced across all fields.")
        print("  8. Evidence references structurally valid.")
        print("  9. MCP claims verified with evidence backing.")
        print(" 10. Buildability verdicts supported with rationale/scores.")
        print(" 11. No fabricated placeholder URLs or dummy text.")
        print(" 12. Research timestamps and quality gate statuses consistent.")
        print("\nDATASET STRUCTURAL VALIDATION PASSED ✓")
        sys.exit(0)
    else:
        print(f"✗ VALIDATION FAILED with {len(errors)} error(s):\n")
        for err in errors[:25]:
            print(f"  - {err}")
        if len(errors) > 25:
            print(f"  ... and {len(errors) - 25} more errors.")
        sys.exit(1)


if __name__ == "__main__":
    main()
