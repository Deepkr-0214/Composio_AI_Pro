#!/usr/bin/env python3
"""
Generate reproducible audit sample and human audit worksheet (Prompt 8).

Selects 20 applications (exactly 2 from each of the 10 categories)
using a deterministic random seed (20261123).
Exports:
- data/audit_sample.json
- data/human_audit_template.csv
"""

import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_FILE = DATA_DIR / "research_results.json"
FIRST_PASS_B1 = DATA_DIR / "batch1_first_pass.json"
FIRST_PASS_B2 = DATA_DIR / "batch2_first_pass.json"
AUDIT_SAMPLE_FILE = DATA_DIR / "audit_sample.json"
AUDIT_TEMPLATE_CSV = DATA_DIR / "human_audit_template.csv"

SEED = 20261123


def load_first_pass_lookup() -> dict[int, dict]:
    """Load original first-pass findings by app_id."""
    lookup = {}
    if FIRST_PASS_B1.exists():
        with open(FIRST_PASS_B1, "r", encoding="utf-8") as f:
            for item in json.load(f):
                lookup[item["app_id"]] = item
    if FIRST_PASS_B2.exists():
        with open(FIRST_PASS_B2, "r", encoding="utf-8") as f:
            for item in json.load(f):
                lookup[item["app_id"]] = item
    return lookup


def select_audit_sample(apps: list[dict], seed: int = SEED) -> list[dict]:
    """Select exactly 2 applications per category deterministically."""
    rng = random.Random(seed)
    categories = {}
    for a in apps:
        categories.setdefault(a["category_name"], []).append(a)

    sample = []
    for cat_name in sorted(categories.keys()):
        cat_apps = categories[cat_name]
        chosen = rng.sample(cat_apps, 2)
        sample.extend(chosen)

    sample.sort(key=lambda x: x["app_id"])
    return sample


def main():
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        apps = json.load(f)

    first_pass_lookup = load_first_pass_lookup()
    sample = select_audit_sample(apps, SEED)

    # 1. Generate data/audit_sample.json
    sample_records = []
    for a in sample:
        aid = a["app_id"]
        fp = first_pass_lookup.get(aid, {})
        sample_records.append({
            "app_id": aid,
            "app_name": a["app_name"],
            "category_name": a["category_name"],
            "first_pass_findings": {
                "auth_methods": fp.get("auth_methods", []),
                "credential_accessibility": fp.get("credential_accessibility", "unknown"),
                "api_type": fp.get("api_type", []),
                "api_breadth": fp.get("api_breadth", "unknown"),
                "mcp_status": fp.get("mcp_status", "unknown"),
                "buildability_verdict": fp.get("buildability_verdict", "unknown"),
                "toolkit_buildability_score": fp.get("toolkit_buildability_score"),
                "quality_gate_status": fp.get("quality_gate_status", "unknown"),
            },
            "latest_findings": {
                "auth_methods": a.get("auth_methods", []),
                "credential_accessibility": a.get("credential_accessibility", "unknown"),
                "api_type": a.get("api_type", []),
                "api_breadth": a.get("api_breadth", "unknown"),
                "mcp_status": a.get("mcp_status", "unknown"),
                "buildability_verdict": a.get("buildability_verdict", "unknown"),
                "toolkit_buildability_score": a.get("toolkit_buildability_score"),
                "quality_gate_status": a.get("quality_gate_status", "unknown"),
            },
            "evidence_links": a.get("evidence_links", []),
            "claim_evidence": a.get("claim_evidence", []),
            "research_notes": a.get("research_notes", ""),
        })

    audit_sample_payload = {
        "metadata": {
            "sampling_method": "stratified_random_by_category",
            "seed": SEED,
            "sample_size": len(sample_records),
            "categories_covered": 10,
            "apps_per_category": 2,
            "selected_app_ids": [r["app_id"] for r in sample_records],
            "description": "Representative 20-app audit sample across all 10 categories for independent human verification."
        },
        "sample": sample_records,
    }

    with open(AUDIT_SAMPLE_FILE, "w", encoding="utf-8") as f:
        json.dump(audit_sample_payload, f, indent=2)
    print(f"Generated {AUDIT_SAMPLE_FILE} ({len(sample_records)} apps)")

    # 2. Generate data/human_audit_template.csv
    csv_fields = [
        "app_id",
        "app_name",
        "category",
        "original_auth_methods",
        "original_credential_access",
        "original_api_surface",
        "original_mcp_status",
        "original_buildability_verdict",
        "corrected_auth_methods",
        "corrected_credential_access",
        "corrected_api_surface",
        "corrected_mcp_status",
        "corrected_buildability_verdict",
        "supporting_source_urls",
        "relevant_documentation_excerpts",
        "human_verified_auth_methods",
        "human_verified_credential_access",
        "human_verified_api_surface",
        "human_verified_mcp_status",
        "human_verified_buildability_verdict",
        "human_evidence_urls",
        "human_reviewer_notes",
        "human_review_timestamp",
        "review_completion_status",
    ]

    with open(AUDIT_TEMPLATE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()

        for r in sample_records:
            fp = r["first_pass_findings"]
            cur = r["latest_findings"]

            urls = [
                link.get("url") if isinstance(link, dict) else str(link)
                for link in r.get("evidence_links", [])
            ]
            excerpts = [
                ce.get("supporting_excerpt", "")
                for ce in r.get("claim_evidence", [])
                if ce.get("supporting_excerpt")
            ]

            writer.writerow({
                "app_id": r["app_id"],
                "app_name": r["app_name"],
                "category": r["category_name"],
                "original_auth_methods": "|".join(fp.get("auth_methods", [])),
                "original_credential_access": fp.get("credential_accessibility", "unknown"),
                "original_api_surface": "|".join(fp.get("api_type", [])),
                "original_mcp_status": fp.get("mcp_status", "unknown"),
                "original_buildability_verdict": fp.get("buildability_verdict", "unknown"),
                "corrected_auth_methods": "|".join(cur.get("auth_methods", [])),
                "corrected_credential_access": cur.get("credential_accessibility", "unknown"),
                "corrected_api_surface": "|".join(cur.get("api_type", [])),
                "corrected_mcp_status": cur.get("mcp_status", "unknown"),
                "corrected_buildability_verdict": cur.get("buildability_verdict", "unknown"),
                "supporting_source_urls": " | ".join(urls),
                "relevant_documentation_excerpts": " -- ".join(excerpts[:2]),
                # Human fields intentionally blank:
                "human_verified_auth_methods": "",
                "human_verified_credential_access": "",
                "human_verified_api_surface": "",
                "human_verified_mcp_status": "",
                "human_verified_buildability_verdict": "",
                "human_evidence_urls": "",
                "human_reviewer_notes": "",
                "human_review_timestamp": "",
                "review_completion_status": "PENDING_HUMAN_REVIEW",
            })

    print(f"Generated {AUDIT_TEMPLATE_CSV} with blank human judgment fields")


if __name__ == "__main__":
    main()
