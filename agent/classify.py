"""
Classification engine for the Composio research agent (Prompt 3).

Classifies applications based on actual documentation evidence into:
- Authentication methods (10 types)
- Credential accessibility (10 types)
- API surface and breadth (5 tiers with justification)
- MCP support status (5 categories)
- Integration buildability verdict (5 tiers with blockers)

Every classification must be traceable to evidence. Unknown is never
treated as a negative finding.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from .models import (
    FindingStatus,
    APIBreadth,
    CredentialAccessibility,
    ConfidenceLevel,
    MCPStatus,
    BuildabilityVerdict,
    BlockerType,
    QualityGateStatus,
)


# ──────────────────────────────────────────────────────────────────────
# Integration Readiness Tiers (kept for backward compatibility)
# ──────────────────────────────────────────────────────────────────────


class IntegrationTier:
    """Integration readiness tiers for applications."""
    READY = "ready"              # Can build integration now
    FEASIBLE = "feasible"        # Possible with some effort
    CHALLENGING = "challenging"  # Significant barriers
    BLOCKED = "blocked"          # Cannot build integration
    UNKNOWN = "unknown"          # Insufficient data


# ──────────────────────────────────────────────────────────────────────
# Buildability Assessment
# ──────────────────────────────────────────────────────────────────────


def assess_buildability(finding: dict) -> dict:
    """
    Assess toolkit buildability based on the classification data.

    Returns a dict with:
      - verdict: BuildabilityVerdict value
      - score: 1-10 numeric score
      - blockers: list of BlockerType values
      - justification: human-readable string
    """
    blockers: list[str] = []
    score = 5  # neutral starting point
    justification_parts: list[str] = []

    # --- Check API availability ---
    api_types = finding.get("api_type", [])
    api_status = finding.get("api_type_status", FindingStatus.UNKNOWN.value)

    if api_status == FindingStatus.CONFIRMED_NO.value:
        blockers.append(BlockerType.NO_PUBLIC_API.value)
        score -= 4
        justification_parts.append("No public API documented.")
    elif not api_types and api_status == FindingStatus.UNKNOWN.value:
        score -= 1
        justification_parts.append("API availability unknown.")
    else:
        has_rest = any(t in ("REST", "GraphQL") for t in api_types)
        if has_rest:
            score += 2
            justification_parts.append(f"Has {', '.join(api_types)} API(s).")
        else:
            score += 1
            justification_parts.append(f"API types: {', '.join(api_types)}.")

    # --- Check authentication ---
    auth_methods = finding.get("auth_methods", [])
    if auth_methods:
        has_standard = any(
            m in ("OAuth2", "API Key", "Bearer Token", "Personal Access Token")
            for m in auth_methods
        )
        if has_standard:
            score += 1
            justification_parts.append(f"Standard auth: {', '.join(auth_methods)}.")
        else:
            justification_parts.append(f"Auth: {', '.join(auth_methods)}.")
    else:
        justification_parts.append("Authentication methods unknown.")

    # --- Check credential accessibility ---
    cred = finding.get("credential_accessibility", CredentialAccessibility.UNKNOWN.value)
    if cred in (
        CredentialAccessibility.FREE_SELF_SERVE.value,
        CredentialAccessibility.TRIAL_SELF_SERVE.value,
    ):
        score += 2
        justification_parts.append("Free/trial self-serve credentials.")
    elif cred == CredentialAccessibility.PAID_SELF_SERVE.value:
        score += 1
        justification_parts.append("Paid self-serve credentials.")
    elif cred in (
        CredentialAccessibility.PARTNER_APPROVAL.value,
        CredentialAccessibility.CONTACT_SALES.value,
        CredentialAccessibility.ENTERPRISE_ONLY.value,
    ):
        blockers.append(BlockerType.CREDENTIAL_BARRIER.value)
        score -= 1
        justification_parts.append(f"Credential access: {cred}.")
    elif cred == CredentialAccessibility.UNKNOWN.value:
        justification_parts.append("Credential accessibility unknown.")

    # --- Check API breadth ---
    breadth = finding.get("api_breadth", APIBreadth.UNKNOWN.value)
    if breadth in (APIBreadth.EXTENSIVE.value, APIBreadth.BROAD.value):
        score += 1
    elif breadth == APIBreadth.NARROW.value:
        score -= 1

    # --- Check MCP status ---
    mcp_status = finding.get("mcp_status", MCPStatus.UNKNOWN.value)
    if mcp_status == MCPStatus.OFFICIAL.value:
        score += 1
        justification_parts.append("Official MCP server available.")
    elif mcp_status == MCPStatus.COMMUNITY.value:
        justification_parts.append("Community MCP server exists.")

    # --- Clamp score ---
    score = max(1, min(10, score))

    # --- Determine verdict ---
    if blockers and any(b in (
        BlockerType.NO_PUBLIC_API.value,
        BlockerType.DEPRECATED_API.value,
    ) for b in blockers):
        verdict = BuildabilityVerdict.NOT_FEASIBLE.value
    elif score >= 8:
        verdict = BuildabilityVerdict.READY_TO_BUILD.value
    elif score >= 6:
        verdict = BuildabilityVerdict.FEASIBLE.value
    elif score >= 4:
        verdict = BuildabilityVerdict.NEEDS_INVESTIGATION.value
    elif score >= 2:
        verdict = BuildabilityVerdict.SIGNIFICANT_BARRIERS.value
    else:
        verdict = BuildabilityVerdict.NOT_FEASIBLE.value

    return {
        "verdict": verdict,
        "score": score,
        "blockers": blockers,
        "justification": " ".join(justification_parts),
    }


# ──────────────────────────────────────────────────────────────────────
# API Breadth Estimation
# ──────────────────────────────────────────────────────────────────────

# Keyword groups that indicate API endpoint variety
_BREADTH_SIGNALS = {
    "crud": [r"\bcreate\b", r"\bread\b", r"\bupdate\b", r"\bdelete\b", r"\blist\b"],
    "entities": [
        r"\busers?\b", r"\bcontacts?\b", r"\baccounts?\b", r"\borders?\b",
        r"\bproducts?\b", r"\btickets?\b", r"\binvoices?\b", r"\bworkflows?\b",
        r"\bevents?\b", r"\bfiles?\b", r"\bmessages?\b", r"\bchannels?\b",
        r"\bwebhooks?\b", r"\bpipelines?\b", r"\bdeals?\b", r"\btasks?\b",
    ],
    "advanced": [
        r"\bbatch\b", r"\bbulk\b", r"\bpagination\b", r"\brate\s*limit\b",
        r"\bsearch\b", r"\bfilter\b", r"\bsort\b", r"\bwebhook\b",
    ],
}


def estimate_api_breadth(text: str) -> dict:
    """
    Estimate API breadth from documentation content.

    Returns:
        dict with 'breadth' (APIBreadth value) and 'justification' string.
    """
    if not text or not text.strip():
        return {"breadth": APIBreadth.UNKNOWN.value, "justification": "No content to analyze."}

    text_lower = text.lower()
    crud_hits = sum(1 for p in _BREADTH_SIGNALS["crud"] if re.search(p, text_lower))
    entity_hits = sum(1 for p in _BREADTH_SIGNALS["entities"] if re.search(p, text_lower))
    advanced_hits = sum(1 for p in _BREADTH_SIGNALS["advanced"] if re.search(p, text_lower))

    total_signals = crud_hits + entity_hits + advanced_hits

    if total_signals >= 12:
        breadth = APIBreadth.EXTENSIVE.value
        justification = f"Extensive API surface: {entity_hits} entity types, {crud_hits} CRUD ops, {advanced_hits} advanced features."
    elif total_signals >= 7:
        breadth = APIBreadth.BROAD.value
        justification = f"Broad API: {entity_hits} entity types, {crud_hits} CRUD ops detected."
    elif total_signals >= 4:
        breadth = APIBreadth.MODERATE.value
        justification = f"Moderate API: {entity_hits} entity types, {crud_hits} CRUD ops."
    elif total_signals >= 1:
        breadth = APIBreadth.NARROW.value
        justification = f"Narrow API: limited signals ({total_signals} total)."
    else:
        breadth = APIBreadth.UNKNOWN.value
        justification = "Insufficient evidence to estimate API breadth."

    return {"breadth": breadth, "justification": justification}


# ──────────────────────────────────────────────────────────────────────
# MCP Classification
# ──────────────────────────────────────────────────────────────────────


def classify_mcp_status(finding: dict) -> dict:
    """
    Classify MCP availability based on evidence in the finding.

    Returns dict with 'mcp_status', 'mcp_repo_url' (if any), 'mcp_notes'.
    """
    mcp_mentioned = finding.get("_mcp_mentioned", False)
    has_official = finding.get("has_official_mcp", FindingStatus.UNKNOWN.value)
    has_community = finding.get("has_community_mcp", FindingStatus.UNKNOWN.value)
    mcp_evidence = finding.get("mcp_evidence", [])

    # Check for official MCP evidence
    if has_official == FindingStatus.CONFIRMED_YES.value:
        repo = ""
        for ev in mcp_evidence:
            if "github.com" in ev.get("url", ""):
                repo = ev["url"]
                break
        return {
            "mcp_status": MCPStatus.OFFICIAL.value,
            "mcp_repo_url": repo,
            "mcp_notes": "Official MCP server confirmed with evidence.",
        }

    # Check for community MCP evidence
    if has_community == FindingStatus.CONFIRMED_YES.value:
        repo = ""
        for ev in mcp_evidence:
            if "github.com" in ev.get("url", ""):
                repo = ev["url"]
                break
        return {
            "mcp_status": MCPStatus.COMMUNITY.value,
            "mcp_repo_url": repo,
            "mcp_notes": "Community MCP server found.",
        }

    # MCP mentioned but not confirmed
    if mcp_mentioned:
        return {
            "mcp_status": MCPStatus.UNVERIFIED_CLAIM.value,
            "mcp_repo_url": "",
            "mcp_notes": "MCP mentioned in documentation but not confirmed with repository evidence.",
        }

    return {
        "mcp_status": MCPStatus.UNKNOWN.value,
        "mcp_repo_url": "",
        "mcp_notes": "No MCP evidence found.",
    }


# ──────────────────────────────────────────────────────────────────────
# Full App Classification
# ──────────────────────────────────────────────────────────────────────


def classify_app(finding: dict, combined_text: str = "") -> dict:
    """
    Perform full classification on a research finding.

    Takes the raw finding dict (with extraction results applied)
    and the combined documentation text. Returns a dict of
    classification fields to merge into the finding.

    Does NOT modify the input finding.
    """
    result: dict = {}

    # 1. API breadth estimation
    breadth_result = estimate_api_breadth(combined_text)
    result["api_breadth"] = breadth_result["breadth"]
    result["api_breadth_notes"] = breadth_result["justification"]
    if breadth_result["breadth"] != APIBreadth.UNKNOWN.value:
        result["api_breadth_status"] = FindingStatus.CONFIRMED_YES.value

    # 2. MCP classification
    mcp_result = classify_mcp_status(finding)
    result["mcp_status"] = mcp_result["mcp_status"]
    result["mcp_repo_url"] = mcp_result.get("mcp_repo_url", "")
    result["mcp_notes"] = mcp_result["mcp_notes"]

    # 3. Buildability assessment
    # Merge breadth into finding copy for assessment
    finding_with_breadth = {**finding, **result}
    build_result = assess_buildability(finding_with_breadth)
    result["buildability_verdict"] = build_result["verdict"]
    result["toolkit_buildability_score"] = build_result["score"]
    result["toolkit_buildability_notes"] = build_result["justification"]
    result["toolkit_buildability"] = (
        FindingStatus.CONFIRMED_YES.value
        if build_result["verdict"] != BuildabilityVerdict.NOT_FEASIBLE.value
        else FindingStatus.CONFIRMED_NO.value
    )
    if build_result["blockers"]:
        result["blockers"] = build_result["blockers"]
        result["blockers_status"] = FindingStatus.CONFIRMED_YES.value

    # 4. Quality gates evaluation
    gate_eval = evaluate_quality_gates(finding_with_breadth)
    result["quality_gate_status"] = gate_eval["status"]
    result["quality_gate_checks"] = gate_eval

    return result


# ──────────────────────────────────────────────────────────────────────
# Legacy classification (backward compatible)
# ──────────────────────────────────────────────────────────────────────


def classify_integration_readiness(finding: dict) -> str:
    """
    Classify an application's integration readiness based on research findings.
    Returns one of the IntegrationTier values.
    """
    if finding.get("overall_confidence") == ConfidenceLevel.UNVERIFIED.value:
        return IntegrationTier.UNKNOWN

    # Use new buildability verdict if available
    verdict = finding.get("buildability_verdict")
    if verdict:
        mapping = {
            BuildabilityVerdict.READY_TO_BUILD.value: IntegrationTier.READY,
            BuildabilityVerdict.FEASIBLE.value: IntegrationTier.FEASIBLE,
            BuildabilityVerdict.NEEDS_INVESTIGATION.value: IntegrationTier.FEASIBLE,
            BuildabilityVerdict.SIGNIFICANT_BARRIERS.value: IntegrationTier.CHALLENGING,
            BuildabilityVerdict.NOT_FEASIBLE.value: IntegrationTier.BLOCKED,
        }
        return mapping.get(verdict, IntegrationTier.UNKNOWN)

    # Fallback to legacy logic
    blockers = finding.get("blockers", [])
    if blockers and finding.get("blockers_status") == FindingStatus.CONFIRMED_YES.value:
        return IntegrationTier.BLOCKED

    api_status = finding.get("api_type_status")
    if api_status == FindingStatus.CONFIRMED_NO.value:
        return IntegrationTier.BLOCKED

    api_breadth = finding.get("api_breadth", APIBreadth.UNKNOWN.value)
    cred_access = finding.get("credential_accessibility", CredentialAccessibility.UNKNOWN.value)

    if api_breadth in (
        APIBreadth.EXTENSIVE.value,
        APIBreadth.BROAD.value,
        APIBreadth.MODERATE.value,
        APIBreadth.COMPREHENSIVE.value,
    ):
        if cred_access in (
            CredentialAccessibility.FREE_SELF_SERVE.value,
            CredentialAccessibility.TRIAL_SELF_SERVE.value,
            CredentialAccessibility.FREE_APPROVAL.value,
        ):
            return IntegrationTier.READY

    if api_breadth in (
        APIBreadth.EXTENSIVE.value,
        APIBreadth.BROAD.value,
        APIBreadth.MODERATE.value,
        APIBreadth.COMPREHENSIVE.value,
    ):
        return IntegrationTier.FEASIBLE

    if api_breadth in (
        APIBreadth.NARROW.value,
        APIBreadth.LIMITED.value,
        APIBreadth.MINIMAL.value,
    ):
        return IntegrationTier.CHALLENGING

    return IntegrationTier.UNKNOWN


# ──────────────────────────────────────────────────────────────────────
# Evidence Quality Validation
# ──────────────────────────────────────────────────────────────────────


def validate_evidence_quality(finding: dict) -> dict:
    """
    Check evidence quality and return warnings.

    Returns dict with:
      - warnings: list of warning strings
      - quality_score: float 0.0-1.0
      - has_critical_gaps: bool
    """
    warnings: list[str] = []
    deductions = 0.0

    app_name = finding.get("app_name", "Unknown")

    # Check evidence links
    evidence = finding.get("evidence_links", [])
    if not evidence:
        warnings.append(f"{app_name}: No evidence links recorded.")
        deductions += 0.3

    # Check for missing URLs in evidence
    for ev in evidence:
        if not ev.get("url"):
            warnings.append(f"{app_name}: Evidence link missing URL.")
            deductions += 0.1

    # Check MCP claims without repo evidence
    mcp_status = finding.get("mcp_status", MCPStatus.UNKNOWN.value)
    if mcp_status in (MCPStatus.OFFICIAL.value, MCPStatus.COMMUNITY.value):
        mcp_repo = finding.get("mcp_repo_url", "")
        if not mcp_repo:
            warnings.append(f"{app_name}: MCP server claimed but no repository URL recorded.")
            deductions += 0.15

    # Check buildability consistency
    verdict = finding.get("buildability_verdict")
    api_status = finding.get("api_type_status", FindingStatus.UNKNOWN.value)
    if verdict == BuildabilityVerdict.READY_TO_BUILD.value and api_status == FindingStatus.UNKNOWN.value:
        warnings.append(f"{app_name}: Buildability 'ready_to_build' but API status is unknown.")
        deductions += 0.2

    # Check auth methods vs credential accessibility
    auth = finding.get("auth_methods", [])
    cred = finding.get("credential_accessibility", CredentialAccessibility.UNKNOWN.value)
    if auth and cred == CredentialAccessibility.UNKNOWN.value:
        warnings.append(f"{app_name}: Auth methods identified but credential accessibility is unknown.")
        deductions += 0.1

    # Confidence assessment
    confidence = finding.get("overall_confidence", ConfidenceLevel.UNVERIFIED.value)
    if confidence == ConfidenceLevel.UNVERIFIED.value:
        deductions += 0.5

    quality_score = max(0.0, min(1.0, 1.0 - deductions))

    return {
        "warnings": warnings,
        "quality_score": round(quality_score, 2),
        "has_critical_gaps": quality_score < 0.5,
    }


def evaluate_quality_gates(finding: dict) -> dict:
    """
    Evaluate formal research quality gates for an application finding.

    Gates:
    1. valid_identity: app_id > 0 and app_name and category_name
    2. has_evidence_links: at least 1 evidence link with url
    3. auth_claims_supported: if auth methods found, claim evidence or source links exist
    4. credential_claims_supported: credential access supported by evidence
    5. mcp_claims_verified: official/community MCP backed by repo URL
    6. buildability_consistency: ready_to_build not asserted without API
    7. confirmed_no_api: flagged if public API confirmed absent

    Returns:
      dict with 'status' (passed, partial, needs_review, blocked),
      'passed_checks', 'failed_checks', and 'summary'.
    """
    passed: list[str] = []
    failed: list[str] = []

    # 1. Identity
    app_id = finding.get("app_id", 0)
    app_name = finding.get("app_name", "")
    cat_name = finding.get("category_name", "")
    if app_id > 0 and app_name and cat_name:
        passed.append("valid_identity")
    else:
        failed.append("valid_identity")

    # 2. Evidence links
    evidence = finding.get("evidence_links", [])
    valid_links = [e for e in evidence if e.get("url")]
    if valid_links:
        passed.append("has_evidence_links")
    else:
        failed.append("has_evidence_links")

    # 3. Auth claims
    auth_methods = finding.get("auth_methods", [])
    claim_ev = finding.get("claim_evidence", [])
    if not auth_methods:
        # None claimed is valid (unknown preserved)
        passed.append("auth_claims_supported")
    else:
        auth_claims = [c for c in claim_ev if c.get("claim_field") == "auth_methods"]
        if auth_claims or valid_links:
            passed.append("auth_claims_supported")
        else:
            failed.append("auth_claims_supported")

    # 4. Credential claims
    cred = finding.get("credential_accessibility", CredentialAccessibility.UNKNOWN.value)
    if cred == CredentialAccessibility.UNKNOWN.value:
        passed.append("credential_claims_supported")
    else:
        cred_claims = [c for c in claim_ev if c.get("claim_field") == "credential_accessibility"]
        if cred_claims or valid_links:
            passed.append("credential_claims_supported")
        else:
            failed.append("credential_claims_supported")

    # 5. MCP claims verified
    mcp_status = finding.get("mcp_status", MCPStatus.UNKNOWN.value)
    if mcp_status in (MCPStatus.OFFICIAL.value, MCPStatus.COMMUNITY.value):
        if finding.get("mcp_repo_url"):
            passed.append("mcp_claims_verified")
        else:
            failed.append("mcp_claims_verified")
    else:
        passed.append("mcp_claims_verified")

    # 6. Buildability consistency
    verdict = finding.get("buildability_verdict")
    api_status = finding.get("api_type_status", FindingStatus.UNKNOWN.value)
    blockers = finding.get("blockers", [])
    if verdict == BuildabilityVerdict.READY_TO_BUILD.value and api_status == FindingStatus.UNKNOWN.value:
        failed.append("buildability_consistency")
    else:
        passed.append("buildability_consistency")

    # 7. Official source present
    has_official = any(
        e.get("source_type") in ("official_documentation", "api_reference", "developer_portal", "github_repository")
        for e in valid_links
    )
    if has_official:
        passed.append("official_source_present")
    else:
        failed.append("official_source_present")

    # Gate status determination
    is_blocked = (
        api_status == FindingStatus.CONFIRMED_NO.value
        or BlockerType.NO_PUBLIC_API.value in blockers
        or verdict == BuildabilityVerdict.NOT_FEASIBLE.value
    )
    confidence = finding.get("overall_confidence", ConfidenceLevel.UNVERIFIED.value)
    has_api = bool(finding.get("api_type")) or api_status == FindingStatus.CONFIRMED_YES.value
    has_auth = bool(finding.get("auth_methods"))

    if is_blocked:
        status = QualityGateStatus.BLOCKED.value
        summary = "Blocked: public API confirmed absent or non-feasible integration."
    elif (
        len(failed) == 0
        and valid_links
        and confidence in (ConfidenceLevel.HIGH.value, ConfidenceLevel.MEDIUM.value)
        and (has_api or has_auth)
    ):
        status = QualityGateStatus.PASSED.value
        summary = f"Passed: all {len(passed)} quality gates satisfied with official evidence."
    elif "mcp_claims_verified" in failed or "buildability_consistency" in failed:
        status = QualityGateStatus.NEEDS_REVIEW.value
        summary = f"Needs Review: discrepancies in {', '.join(failed)}."
    elif valid_links:
        status = QualityGateStatus.PARTIAL.value
        summary = f"Partial: preliminary evidence gathered ({len(passed)} passed, {len(failed)} gaps)."
    else:
        status = QualityGateStatus.NEEDS_REVIEW.value
        summary = "Needs Review: no verifiable evidence collected."

    return {
        "status": status,
        "passed_checks": passed,
        "failed_checks": failed,
        "summary": summary,
    }


# ──────────────────────────────────────────────────────────────────────
# Category Summary
# ──────────────────────────────────────────────────────────────────────


def get_category_summary(findings: list[dict]) -> dict:
    """
    Generate summary statistics for a category of findings.
    """
    total = len(findings)
    if total == 0:
        return {}

    tiers = {}
    for f in findings:
        tier = classify_integration_readiness(f)
        tiers[tier] = tiers.get(tier, 0) + 1

    # MCP counts
    mcp_official = sum(
        1 for f in findings
        if f.get("mcp_status") == MCPStatus.OFFICIAL.value
    )
    mcp_community = sum(
        1 for f in findings
        if f.get("mcp_status") == MCPStatus.COMMUNITY.value
    )
    mcp_any = sum(
        1 for f in findings
        if f.get("mcp_status") in (MCPStatus.OFFICIAL.value, MCPStatus.COMMUNITY.value)
        or f.get("has_official_mcp") == FindingStatus.CONFIRMED_YES.value
        or f.get("has_community_mcp") == FindingStatus.CONFIRMED_YES.value
    )

    # Buildability distribution
    build_dist: dict[str, int] = {}
    for f in findings:
        v = f.get("buildability_verdict", BuildabilityVerdict.UNKNOWN.value)
        build_dist[v] = build_dist.get(v, 0) + 1

    # Auth method distribution
    auth_dist: dict[str, int] = {}
    for f in findings:
        for m in f.get("auth_methods", []):
            auth_dist[m] = auth_dist.get(m, 0) + 1

    return {
        "total_apps": total,
        "tier_distribution": tiers,
        "has_mcp_count": mcp_any,
        "mcp_official_count": mcp_official,
        "mcp_community_count": mcp_community,
        "buildability_distribution": build_dist,
        "auth_method_distribution": auth_dist,
        "avg_buildability_score": _safe_avg([
            f.get("toolkit_buildability_score")
            for f in findings
            if f.get("toolkit_buildability_score") is not None
        ]),
    }


def _safe_avg(values: list) -> Optional[float]:
    """Calculate average, returning None if no valid values."""
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)
