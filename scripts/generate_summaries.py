#!/usr/bin/env python3
"""
Generate research metrics, category summaries, and verification candidates
from data/research_results.json.
"""

import json
from pathlib import Path
from collections import Counter
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
RESULTS_FILE = ROOT / "data" / "research_results.json"
SOURCES_FILE = ROOT / "data" / "source_records.json"


def main():
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    sources = []
    if SOURCES_FILE.exists():
        with open(SOURCES_FILE, "r", encoding="utf-8") as f:
            sources = json.load(f)

    # --- STEP 9: RESEARCH METRICS ---
    total_apps = len(data)
    attempted = sum(1 for a in data if a.get("researched_at"))
    passed = sum(1 for a in data if a.get("quality_gate_status") == "passed")
    partial = sum(1 for a in data if a.get("quality_gate_status") == "partial")
    blocked = sum(1 for a in data if a.get("quality_gate_status") == "blocked")
    needs_review = sum(1 for a in data if a.get("quality_gate_status") == "needs_review")

    has_oauth2 = sum(1 for a in data if "OAuth2" in a.get("auth_methods", []))
    has_api_key = sum(1 for a in data if "API Key" in a.get("auth_methods", []))
    multi_auth = sum(1 for a in data if len(a.get("auth_methods", [])) > 1)

    official_mcp = sum(1 for a in data if a.get("mcp_status") == "official_mcp")
    community_mcp = sum(1 for a in data if a.get("mcp_status") == "community_mcp")
    unverified_mcp = sum(1 for a in data if a.get("mcp_status") == "mcp_unverified")
    unknown_mcp = sum(1 for a in data if a.get("mcp_status") in ("unknown", None))

    buildable_now = sum(1 for a in data if a.get("buildability_verdict") == "ready_to_build")
    feasible = sum(1 for a in data if a.get("buildability_verdict") == "feasible")
    needs_investigation = sum(1 for a in data if a.get("buildability_verdict") == "needs_investigation")
    significant_barriers = sum(1 for a in data if a.get("buildability_verdict") == "significant_barriers")
    not_feasible = sum(1 for a in data if a.get("buildability_verdict") == "not_feasible")
    unknown_buildability = sum(1 for a in data if a.get("buildability_verdict") in ("unknown", None))

    requires_approval_outreach = sum(
        1 for a in data if a.get("credential_accessibility") in (
            "admin_approval", "app_review_required", "partner_approval", "contact_sales", "enterprise_only"
        )
    )
    blocked_by_missing_surface = sum(
        1 for a in data if "no_public_api" in a.get("blockers", []) or a.get("buildability_verdict") == "significant_barriers"
    )

    durations = [a.get("research_duration_seconds", 0) for a in data if a.get("research_duration_seconds")]
    total_exec_time = sum(durations)
    avg_exec_time = total_exec_time / len(durations) if durations else 0

    evidence_counts = [len(a.get("evidence_links", [])) for a in data if isinstance(a.get("evidence_links"), list)]
    apps_with_evidence = sum(1 for c in evidence_counts if c > 0)
    evidence_cov_pct = round((apps_with_evidence / total_apps) * 100, 2)

    metrics = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "dataset_scope": "100 Applications across 10 Categories",
            "note": "These are operational pipeline metrics, not verified ground-truth accuracy percentages."
        },
        "totals": {
            "total_applications": total_apps,
            "applications_attempted": attempted,
            "quality_gate_passed": passed,
            "quality_gate_partial": partial,
            "quality_gate_needs_review": needs_review,
            "quality_gate_blocked": blocked,
        },
        "documentation_and_evidence": {
            "applications_with_documentation_evidence": apps_with_evidence,
            "evidence_coverage_percentage": evidence_cov_pct,
            "total_source_records_stored": len(sources),
            "applications_with_official_api_docs_url": sum(1 for a in data if a.get("api_docs_url")),
        },
        "authentication_findings": {
            "with_oauth2_evidence": has_oauth2,
            "with_api_key_evidence": has_api_key,
            "with_multiple_auth_methods": multi_auth,
            "auth_identified_total": sum(1 for a in data if a.get("auth_methods")),
            "auth_unknown_total": sum(1 for a in data if not a.get("auth_methods")),
        },
        "mcp_findings": {
            "confirmed_official_mcp": official_mcp,
            "confirmed_community_mcp": community_mcp,
            "unverified_mcp_claims": unverified_mcp,
            "unknown_mcp_status": unknown_mcp,
        },
        "buildability_and_barriers": {
            "ready_to_build_score_8_10": buildable_now,
            "feasible_score_6_7": feasible,
            "needs_investigation_score_4_5": needs_investigation,
            "significant_barriers_score_2_3": significant_barriers,
            "not_feasible_score_1": not_feasible,
            "unknown_buildability": unknown_buildability,
            "requires_approval_or_outreach": requires_approval_outreach,
            "blocked_by_missing_surfaces": blocked_by_missing_surface,
        },
        "execution_performance": {
            "total_measured_execution_seconds": round(total_exec_time, 2),
            "average_duration_seconds_per_app": round(avg_exec_time, 2),
        }
    }

    with open(ROOT / "data" / "research_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print("Generated data/research_metrics.json")

    # --- STEP 10: CATEGORY LEVEL SUMMARY ---
    categories_summary = {}
    cat_groups = {}
    for a in data:
        cat = a.get("category_name", "Unknown")
        cat_groups.setdefault(cat, []).append(a)

    for cat_name, apps in cat_groups.items():
        auth_dist = Counter()
        for a in apps:
            for am in a.get("auth_methods", []):
                auth_dist[am] += 1
            if not a.get("auth_methods"):
                auth_dist["unknown"] += 1

        cred_dist = Counter(a.get("credential_accessibility", "unknown") for a in apps)
        api_dist = Counter()
        for a in apps:
            for at in a.get("api_type", []):
                api_dist[at] += 1
            if not a.get("api_type"):
                api_dist["unknown"] += 1

        mcp_dist = Counter(a.get("mcp_status", "unknown") for a in apps)
        build_dist = Counter(a.get("buildability_verdict", "unknown") for a in apps)

        blockers_dist = Counter()
        for a in apps:
            for blk in a.get("blockers", []):
                blockers_dist[blk] += 1

        gates_dist = Counter(a.get("quality_gate_status", "unknown") for a in apps)
        missing_ev = sum(1 for a in apps if not a.get("evidence_links"))
        complete_count = sum(1 for a in apps if a.get("quality_gate_status") == "passed")

        categories_summary[cat_name] = {
            "total_applications": len(apps),
            "category_id": apps[0].get("category_id") if apps else None,
            "research_completeness_rate": f"{round(complete_count / len(apps) * 100, 1)}%",
            "quality_gate_distribution": dict(gates_dist),
            "authentication_methods_distribution": dict(auth_dist),
            "credential_accessibility_distribution": dict(cred_dist),
            "api_surfaces_distribution": dict(api_dist),
            "mcp_availability_distribution": dict(mcp_dist),
            "buildability_verdict_distribution": dict(build_dist),
            "most_frequent_blockers": dict(blockers_dist.most_common(5)),
            "apps_missing_documentation_evidence": missing_ev,
            "average_buildability_score": round(
                sum(a.get("toolkit_buildability_score", 0) for a in apps) / len(apps), 2
            ) if apps else 0,
        }

    with open(ROOT / "data" / "category_summary.json", "w", encoding="utf-8") as f:
        json.dump(categories_summary, f, indent=2)
    print("Generated data/category_summary.json (10 categories)")

    # --- STEP 11: VERIFICATION CANDIDATES ---
    ambiguous_ids = {58, 98, 91, 84, 85, 94, 90, 99}
    candidates = []
    audit_per_category = {}

    for a in data:
        reasons = []
        app_id = a["app_id"]
        cat = a["category_name"]

        # Priority 1: Specific nonstandard applications
        if app_id in ambiguous_ids:
            reasons.append("Nonstandard integration surface (CLI, enterprise-only, or ambiguous vendor identity)")

        # Priority 2: Quality gate needs review or low confidence
        if a.get("quality_gate_status") == "needs_review":
            reasons.append("Quality gate: needs_review (no discoverable docs or blocked by WAF)")
        elif a.get("overall_confidence") == "low":
            reasons.append("Low confidence classification")

        # Priority 3: MCP claim audit
        mcp_st = a.get("mcp_status")
        if mcp_st in ("official_mcp", "community_mcp", "mcp_unverified"):
            reasons.append(f"MCP claim audit: {mcp_st}")

        # Priority 4: High buildability score claims
        b_score = a.get("toolkit_buildability_score", 0)
        if b_score >= 9:
            reasons.append(f"High buildability score audit: {b_score}/10")

        # Priority 5: Complex or multiple auth
        if len(a.get("auth_methods", [])) >= 2:
            reasons.append("Multiple documented authentication methods")

        if reasons:
            candidates.append({
                "app_id": app_id,
                "app_name": a["app_name"],
                "category_name": cat,
                "current_verdict": a.get("buildability_verdict"),
                "current_quality_gate": a.get("quality_gate_status"),
                "reasons_for_review": reasons,
                "candidate_type": "targeted_investigation"
            })

        # Stratified sample: select first app per category for baseline audit
        if cat not in audit_per_category:
            audit_per_category[cat] = {
                "app_id": app_id,
                "app_name": a["app_name"],
                "category_name": cat,
                "current_verdict": a.get("buildability_verdict"),
                "current_quality_gate": a.get("quality_gate_status"),
                "candidate_type": "stratified_category_audit",
                "reasons_for_review": ["Stratified category baseline audit"]
            }

    stratified_sample = list(audit_per_category.values())

    verification_plan = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_targeted_candidates": len(candidates),
            "total_stratified_audit_candidates": len(stratified_sample),
            "note": "Candidate pool for Prompt 7 verification workflows. Accuracy is not pre-calculated here."
        },
        "targeted_candidates": candidates,
        "stratified_category_sample": stratified_sample,
    }

    with open(ROOT / "data" / "verification_candidates.json", "w", encoding="utf-8") as f:
        json.dump(verification_plan, f, indent=2)
    print(f"Generated data/verification_candidates.json ({len(candidates)} targeted, {len(stratified_sample)} stratified)")


if __name__ == "__main__":
    main()
