#!/usr/bin/env python3
"""
Accuracy scoring engine for the research agent (Prompt 8).

Compares:
A. Original first-pass classifications
B. Corrected classifications after automated verification
C. Actual human-reviewed reference classifications

Evaluates five core dimensions:
1. Authentication methods (normalized set comparison)
2. Credential accessibility (normalized tier match)
3. API surface (normalized set comparison)
4. MCP status (exact match)
5. Buildability verdict (exact match)

HONESTY GUARANTEE:
If no genuine human judgments exist, returns status as "NOT MEASURED".
Never fabricates human accuracy scores.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
AUDIT_SAMPLE_FILE = DATA_DIR / "audit_sample.json"
AUDIT_CSV_FILE = DATA_DIR / "human_audit_template.csv"
FIRST_PASS_B1 = DATA_DIR / "batch1_first_pass.json"
FIRST_PASS_B2 = DATA_DIR / "batch2_first_pass.json"
RESULTS_FILE = DATA_DIR / "research_results.json"
ACCURACY_REPORT_FILE = DATA_DIR / "accuracy_report.json"

DIMENSIONS = [
    "auth_methods",
    "credential_accessibility",
    "api_type",
    "mcp_status",
    "buildability_verdict",
]


def normalize_value(dim: str, val: Any) -> Any:
    """Normalize values for fair, robust comparison."""
    if val is None or val == "":
        return None

    if dim in ("auth_methods", "api_type"):
        if isinstance(val, str):
            parts = [p.strip() for p in val.replace("|", ",").split(",") if p.strip()]
            return set(parts)
        elif isinstance(val, (list, set)):
            return set(str(v).strip() for v in val if str(v).strip())
        return set()

    return str(val).strip().lower()


def compare_dimension(dim: str, agent_val: Any, human_val: Any) -> bool:
    """Compare agent classification to human ground truth."""
    norm_agent = normalize_value(dim, agent_val)
    norm_human = normalize_value(dim, human_val)

    if norm_human is None:
        return False

    if dim in ("auth_methods", "api_type"):
        # For sets: must have non-empty intersection and human labels covered
        if not norm_agent and not norm_human:
            return True
        if not norm_agent or not norm_human:
            return False
        # Exact set equality or subset matching
        return norm_agent == norm_human

    return norm_agent == norm_human


def score_audit_dataset(
    human_reviews: list[dict],
    first_pass_lookup: dict[int, dict],
    corrected_lookup: dict[int, dict],
) -> dict:
    """
    Score human-reviewed judgments against first-pass and corrected findings.
    """
    scorable_pairs = 0
    excluded_unverifiable = 0
    first_pass_correct = 0
    corrected_correct = 0

    dim_stats = {
        d: {
            "scorable": 0,
            "first_pass_correct": 0,
            "corrected_correct": 0,
            "improved": 0,
            "regressed": 0,
            "unchanged": 0,
        }
        for d in DIMENSIONS
    }

    improved_classifications = []
    regressed_classifications = []
    unchanged_classifications = []

    for review in human_reviews:
        aid = review.get("app_id")
        app_name = review.get("app_name", f"App {aid}")

        # Check if review has completion status
        completion = str(review.get("review_completion_status", "")).strip().upper()
        if completion == "PENDING_HUMAN_REVIEW" or not review.get("human_verified"):
            # Check if any human field is populated
            has_human_data = any(
                review.get(f"human_verified_{d}")
                for d in ("auth_methods", "credential_access", "api_surface", "mcp_status", "buildability_verdict")
            )
            if not has_human_data:
                continue

        fp = first_pass_lookup.get(aid, {})
        cur = corrected_lookup.get(aid, {})

        for dim in DIMENSIONS:
            # Map dimension names to review field names
            h_field = f"human_verified_{dim}"
            if dim == "credential_accessibility":
                h_field = "human_verified_credential_access"
            elif dim == "api_type":
                h_field = "human_verified_api_surface"
            elif dim == "buildability_verdict":
                h_field = "human_verified_buildability_verdict"

            human_val = review.get(h_field)
            if human_val in ("UNVERIFIABLE", "unverifiable"):
                excluded_unverifiable += 1
                continue

            if human_val is None or human_val == "":
                continue

            scorable_pairs += 1
            dim_stats[dim]["scorable"] += 1

            fp_val = fp.get(dim)
            cur_val = cur.get(dim)

            fp_match = compare_dimension(dim, fp_val, human_val)
            cur_match = compare_dimension(dim, cur_val, human_val)

            if fp_match:
                first_pass_correct += 1
                dim_stats[dim]["first_pass_correct"] += 1
            if cur_match:
                corrected_correct += 1
                dim_stats[dim]["corrected_correct"] += 1

            item_info = {
                "app_id": aid,
                "app_name": app_name,
                "dimension": dim,
                "first_pass_value": fp_val,
                "corrected_value": cur_val,
                "human_reference_value": human_val,
            }

            if cur_match and not fp_match:
                dim_stats[dim]["improved"] += 1
                improved_classifications.append(item_info)
            elif not cur_match and fp_match:
                dim_stats[dim]["regressed"] += 1
                regressed_classifications.append(item_info)
            else:
                dim_stats[dim]["unchanged"] += 1
                unchanged_classifications.append(item_info)

    if scorable_pairs == 0:
        return {
            "status": "HUMAN_AUDIT_PENDING",
            "status_message": "HUMAN AUDIT PENDING — ACCURACY NOT YET MEASURED.",
            "completed_human_reviews": 0,
            "scorable_app_field_pairs": 0,
            "excluded_unverifiable_pairs": excluded_unverifiable,
            "first_pass_correct": 0,
            "corrected_correct": 0,
            "first_pass_accuracy": None,
            "corrected_accuracy": None,
            "accuracy_improvement_points": None,
            "dimension_breakdown": dim_stats,
            "improved_count": 0,
            "regressed_count": 0,
            "unchanged_count": 0,
        }

    fp_acc = round(first_pass_correct / scorable_pairs * 100, 2)
    cur_acc = round(corrected_correct / scorable_pairs * 100, 2)
    improvement = round(cur_acc - fp_acc, 2)

    return {
        "status": "MEASURED",
        "status_message": f"Measured accuracy on {scorable_pairs} scorable human-reviewed pairs.",
        "completed_human_reviews": len(human_reviews),
        "scorable_app_field_pairs": scorable_pairs,
        "excluded_unverifiable_pairs": excluded_unverifiable,
        "first_pass_correct": first_pass_correct,
        "corrected_correct": corrected_correct,
        "first_pass_accuracy": fp_acc,
        "corrected_accuracy": cur_acc,
        "accuracy_improvement_points": improvement,
        "dimension_breakdown": dim_stats,
        "improved_count": len(improved_classifications),
        "regressed_count": len(regressed_classifications),
        "unchanged_count": len(unchanged_classifications),
        "improved_examples": improved_classifications[:5],
        "regressed_examples": regressed_classifications[:5],
    }


def load_first_pass_lookup() -> dict[int, dict]:
    lookup = {}
    for p in (FIRST_PASS_B1, FIRST_PASS_B2):
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    lookup[item["app_id"]] = item
    return lookup


def load_human_reviews_from_csv(csv_path: Path = AUDIT_CSV_FILE) -> list[dict]:
    """Load human audit records from CSV."""
    reviews = []
    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                reviews.append(row)
    return reviews


def generate_accuracy_report(
    sample_file: Path = AUDIT_SAMPLE_FILE,
    csv_file: Path = AUDIT_CSV_FILE,
    output_file: Path = ACCURACY_REPORT_FILE,
) -> dict:
    """Run accuracy calculation and persist data/accuracy_report.json."""
    first_pass_lookup = load_first_pass_lookup()

    corrected_lookup = {}
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            for item in json.load(f):
                corrected_lookup[item["app_id"]] = item

    human_reviews = load_human_reviews_from_csv(csv_file)
    sample_meta = {}
    if sample_file.exists():
        with open(sample_file, "r", encoding="utf-8") as f:
            sample_meta = json.load(f).get("metadata", {})

    metrics = score_audit_dataset(human_reviews, first_pass_lookup, corrected_lookup)

    report = {
        "metadata": {
            "report_name": "Human Audit Ground-Truth Accuracy Report",
            "sample_size": sample_meta.get("sample_size", 20),
            "sampling_method": sample_meta.get("sampling_method", "stratified_random_by_category"),
            "sampling_seed": sample_meta.get("seed", 20261123),
            "categories_covered": 10,
            "apps_per_category": 2,
            "note": "Strict honesty guarantee: accuracy is NOT MEASURED until genuine human reviews are logged."
        },
        "accuracy_evaluation": metrics,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved accuracy report to {output_file}")
    return report


def main() -> None:
    print("=" * 60)
    print("ACCURACY SCORING ENGINE — HUMAN AUDIT GROUND TRUTH")
    print("=" * 60)

    report = generate_accuracy_report()
    acc = report["accuracy_evaluation"]

    print(f"\nStatus: {acc['status_message']}")
    print(f"  Scorable App-Field Pairs:        {acc['scorable_app_field_pairs']}")
    print(f"  Excluded Unverifiable Pairs:     {acc['excluded_unverifiable_pairs']}")
    print(f"  First-Pass Accuracy:             {acc['first_pass_accuracy']}")
    print(f"  Corrected Accuracy:              {acc['corrected_accuracy']}")
    print(f"  Accuracy Improvement:            {acc['accuracy_improvement_points']}")
    print(f"\nSaved Report:")
    print(f"  - {ACCURACY_REPORT_FILE.name}\n")


if __name__ == "__main__":
    main()
