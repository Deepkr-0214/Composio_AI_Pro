"""
Core research engine for the Composio research agent.

Handles automated investigation of applications, gathering data about
APIs, authentication, MCP support, and integration feasibility.

Supports:
- Deterministic keyword-based extraction (no API key required)
- Optional LLM-based extraction (configurable provider)
- Resume from previous progress
- First-pass / correction traceability
- Claim-level evidence (Prompt 3)
- Classification integration (Prompt 3)
- Per-app timing (Prompt 3)
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import (
    ResearchFinding,
    create_empty_finding,
    FindingStatus,
    ConfidenceLevel,
    APIType,
    AuthMethod,
    APIBreadth,
    CredentialAccessibility,
    MCPStatus,
    BuildabilityVerdict,
    ClaimEvidence,
)
from .sources import (
    SourceRecord,
    FetchStatus,
    discover_all_candidate_sources,
    discover_known_sources,
    load_source_records,
    save_source_records,
    merge_source_records,
    get_source_records_for_app,
)
from .fetcher import DocumentationFetcher
from .classify import classify_app, validate_evidence_quality

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
APPS_FILE = DATA_DIR / "apps.json"
RESULTS_FILE = DATA_DIR / "research_results.json"
FIRST_PASS_FILE = DATA_DIR / "first_pass_results.json"
CSV_FILE = DATA_DIR / "research_results.csv"
PILOT_FIRST_PASS_FILE = DATA_DIR / "pilot_first_pass.json"
PILOT_CSV_FILE = DATA_DIR / "pilot_results.csv"
PILOT_METRICS_FILE = DATA_DIR / "pilot_metrics.json"

PILOT_APP_IDS = [1, 11, 21, 31, 41, 55, 61, 71, 81, 96]


# ---------------------------------------------------------------------------
# Data loading / saving
# ---------------------------------------------------------------------------


def load_apps() -> dict:
    """Load the applications dataset."""
    with open(APPS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_results() -> list[dict]:
    """Load existing research results, or return empty list."""
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    return []


def save_results(results: list[dict]) -> None:
    """Save research results to disk."""
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def save_first_pass(results: list[dict]) -> None:
    """Save first-pass results separately for verification traceability."""
    FIRST_PASS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FIRST_PASS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def load_first_pass() -> list[dict]:
    """Load first-pass results."""
    if FIRST_PASS_FILE.exists():
        with open(FIRST_PASS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def export_csv(results: list[dict], filepath: Optional[Path] = None) -> None:
    """Export research results to CSV."""
    if not results:
        return
    out_file = filepath or CSV_FILE
    out_file.parent.mkdir(parents=True, exist_ok=True)
    flat_fields = [
        "app_id", "app_name", "category_name",
        "auth_methods", "credential_accessibility",
        "api_type", "api_breadth", "api_breadth_notes",
        "mcp_status", "mcp_repo_url",
        "buildability_verdict", "toolkit_buildability_score",
        "overall_confidence", "quality_gate_status",
        "researched_at",
    ]
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=flat_fields, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            row = dict(r)
            # Flatten lists to comma-separated
            for k in ("auth_methods", "api_type", "blockers"):
                if isinstance(row.get(k), list):
                    row[k] = ", ".join(str(v) for v in row[k])
            writer.writerow(row)


def save_pilot_first_pass(results: list[dict]) -> None:
    """Save pilot first-pass snapshot (preserves original for verification)."""
    if not PILOT_FIRST_PASS_FILE.exists():
        PILOT_FIRST_PASS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PILOT_FIRST_PASS_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved initial pilot first-pass snapshot to {PILOT_FIRST_PASS_FILE}")


def calculate_pilot_metrics(pilot_results: list[dict], concurrency: int = 5) -> dict:
    """
    Calculate operational completeness and quality metrics for the 10-app pilot.
    These are pipeline quality metrics, NOT fabricated ground-truth accuracy.
    """
    total = len(pilot_results)
    if total == 0:
        return {}

    passed_count = sum(1 for r in pilot_results if r.get("quality_gate_status") == "passed")
    partial_count = sum(1 for r in pilot_results if r.get("quality_gate_status") == "partial")
    needs_review_count = sum(1 for r in pilot_results if r.get("quality_gate_status") == "needs_review")
    blocked_count = sum(1 for r in pilot_results if r.get("quality_gate_status") == "blocked")

    with_official = sum(
        1 for r in pilot_results
        if any(e.get("source_type") in ("official_documentation", "api_reference", "developer_portal", "github_repository")
               for e in r.get("evidence_links", []))
    )
    missing_auth = sum(1 for r in pilot_results if not r.get("auth_methods"))
    missing_creds = sum(1 for r in pilot_results if r.get("credential_accessibility") == "unknown")
    unresolved_mcp = sum(1 for r in pilot_results if r.get("mcp_status") in ("unknown", "mcp_unverified"))

    durations = [r.get("research_duration_seconds") for r in pilot_results if r.get("research_duration_seconds") is not None]
    avg_dur = round(sum(durations) / len(durations), 2) if durations else 0.0
    total_dur = round(sum(durations), 2) if durations else 0.0

    # Estimate 100-app full execution time (parallelism factor ~ concurrency / 1.5 due to IO)
    effective_concurrency = max(1, concurrency - 1)
    est_100_seconds = round((avg_dur * 100) / effective_concurrency, 1)
    est_100_minutes = round(est_100_seconds / 60, 1)

    metrics = {
        "pilot_timestamp": datetime.now(timezone.utc).isoformat(),
        "applications_attempted": total,
        "successfully_passed_quality_gates": passed_count,
        "partially_processed": partial_count,
        "needs_review": needs_review_count,
        "blocked": blocked_count,
        "with_official_documentation_evidence": with_official,
        "missing_authentication_evidence": missing_auth,
        "missing_credential_access_evidence": missing_creds,
        "unresolved_mcp_status": unresolved_mcp,
        "average_duration_seconds_per_app": avg_dur,
        "total_pilot_execution_seconds": total_dur,
        "estimated_full_100_apps_seconds": est_100_seconds,
        "estimated_full_100_apps_minutes": est_100_minutes,
        "estimation_rationale": (
            f"Based on {total} pilot apps averaging {avg_dur}s per app across {concurrency} workers, "
            f"scaled to 100 apps with IO scheduling overhead."
        ),
    }

    PILOT_METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PILOT_METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    return metrics


# ---------------------------------------------------------------------------
# Initialize / resume
# ---------------------------------------------------------------------------


def initialize_results() -> list[dict]:
    """
    Initialize empty research results for all 100 applications.
    Every field starts as 'unknown' — nothing is fabricated.
    """
    apps_data = load_apps()
    categories = {c["id"]: c["name"] for c in apps_data["categories"]}
    results = []

    for app in apps_data["applications"]:
        finding = create_empty_finding(
            app_id=app["id"],
            app_name=app["name"],
            category_id=app["category_id"],
            category_name=categories[app["category_id"]],
        )
        results.append(finding.to_dict())

    save_results(results)
    return results


def get_or_initialize_results() -> list[dict]:
    """Load existing results or initialize fresh ones."""
    results = load_results()
    if not results:
        results = initialize_results()
    return results


def get_research_progress() -> dict:
    """Get a summary of research progress."""
    results = load_results()
    if not results:
        return {"total": 0, "researched": 0, "verified": 0, "percent_researched": 0.0}

    total = len(results)
    researched = sum(
        1 for r in results
        if r.get("overall_confidence") != ConfidenceLevel.UNVERIFIED.value
    )
    verified = sum(1 for r in results if r.get("verified_at"))

    return {
        "total": total,
        "researched": researched,
        "verified": verified,
        "percent_researched": round(researched / total * 100, 1) if total else 0,
        "percent_verified": round(verified / total * 100, 1) if total else 0,
    }


# ---------------------------------------------------------------------------
# Deterministic keyword-based extraction (no LLM required)
# ---------------------------------------------------------------------------


# Pattern maps for keyword extraction from documentation text
AUTH_PATTERNS = {
    "OAuth2": [r"\boauth\s*2?\b", r"\boauth2\b", r"\bauthorization\s+code\b"],
    "API Key": [r"\bapi[\s_-]?key\b", r"\bx-api-key\b"],
    "Bearer Token": [r"\bbearer\s+token\b", r"\bauthorization:\s*bearer\b"],
    "Basic Auth": [r"\bbasic\s+auth\b", r"\bhttp\s+basic\b"],
    "Personal Access Token": [
        r"\bpersonal\s+access\s+token\b",
        r"\bpat\b.*\btoken\b",
    ],
    "Service Account": [
        r"\bservice\s+account\b",
        r"\bservice\s+credentials?\b",
    ],
    "JWT": [r"\bjwt\b", r"\bjson\s+web\s+token\b"],
    "HMAC": [r"\bhmac\b"],
    "Session Based": [r"\bsession\s+(based|cookie|auth)\b", r"\bsession\s+token\b"],
    "Webhook": [r"\bwebhook\s+sign\b", r"\bwebhook\s+secret\b"],
}

API_TYPE_PATTERNS = {
    "REST": [r"\brest\s*api\b", r"\brestful\b", r"\brest\b"],
    "GraphQL": [r"\bgraphql\b", r"\bgraph\s+ql\b"],
    "gRPC": [r"\bgrpc\b"],
    "SOAP": [r"\bsoap\b", r"\bwsdl\b"],
    "WebSocket": [r"\bwebsocket\b", r"\bwss?://\b"],
    "Webhook": [r"\bwebhook\b"],
}

CREDENTIAL_PATTERNS = {
    "free_self_serve": [
        r"\bfree\s+(tier|plan|account)\b",
        r"\bsign\s+up\s+(for\s+)?free\b",
        r"\bfree\s+api\b",
        r"\bno\s+credit\s+card\b",
        r"\bfree\s+developer\b",
        r"\bfree\s+to\s+use\b",
    ],
    "trial_self_serve": [
        r"\bfree\s+trial\b",
        r"\btrial\s+(account|period|plan)\b",
        r"\btry\s+(for\s+)?free\b",
    ],
    "paid_self_serve": [
        r"\bpaid\s+(plan|tier)\b",
        r"\bpricing\b.*\bapi\b",
        r"\bsubscription\s+required\b",
        r"\bpay[\s-]?as[\s-]?you[\s-]?go\b",
    ],
    "admin_approval": [
        r"\badmin\s+approval\b",
        r"\borganization\s+admin\b",
        r"\bworkspace\s+admin\b",
    ],
    "app_review_required": [
        r"\bapp\s+review\b",
        r"\breview\s+process\b",
        r"\bsubmit\s+(for\s+)?review\b",
    ],
    "partner_approval": [
        r"\bpartner\s+(program|only|access|approval)\b",
    ],
    "enterprise_only": [
        r"\benterprise\s+(only|plan|contact)\b",
        r"\bcontact\s+sales\b.*\benterprise\b",
    ],
    "contact_sales": [
        r"\bcontact\s+sales\b.*\bapi\b",
        r"\bcontact\s+us\s+for\s+api\b",
    ],
}

# MCP-specific patterns
MCP_PATTERNS = {
    "official_mcp": [
        r"\bofficial\s+mcp\b",
        r"\bmcp\s+server\b.*\bofficial\b",
        r"\bmodel\s+context\s+protocol\b.*\bofficial\b",
    ],
    "community_mcp": [
        r"\bcommunity\s+mcp\b",
        r"\bunofficial\s+mcp\b",
    ],
    "mcp_mentioned": [
        r"\bmcp\b.*\bserver\b",
        r"\bmodel\s+context\s+protocol\b",
        r"\bmcp\b.*\btool\b",
    ],
}


def _search_patterns(text: str, patterns: dict[str, list[str]]) -> list[str]:
    """Search text for pattern matches, return list of matched keys."""
    text_lower = text.lower()
    matches = []
    for key, pats in patterns.items():
        for pat in pats:
            if re.search(pat, text_lower, re.IGNORECASE):
                matches.append(key)
                break
    return matches


def _find_supporting_excerpt(text: str, pattern: str, context_chars: int = 150) -> str:
    """Find a supporting excerpt around a pattern match."""
    text_lower = text.lower()
    match = re.search(pattern, text_lower, re.IGNORECASE)
    if not match:
        return ""
    start = max(0, match.start() - context_chars)
    end = min(len(text), match.end() + context_chars)
    excerpt = text[start:end].strip()
    # Clean up: remove excessive whitespace
    excerpt = re.sub(r"\s+", " ", excerpt)
    return excerpt[:300]


def extract_from_content(source_records: list[dict]) -> dict:
    """
    Extract research fields from fetched source content using
    deterministic keyword matching. No LLM required.

    Returns a dict of extracted fields (only fields with evidence),
    including claim-level evidence (Prompt 3).
    """
    # Combine all successfully fetched content
    combined_text = ""
    evidence_links = []
    source_map: list[dict] = []  # for claim-level evidence

    for rec in source_records:
        if rec.get("fetch_status") == FetchStatus.SUCCESS.value:
            excerpt = rec.get("content_excerpt", "")
            if excerpt:
                combined_text += f"\n{excerpt}\n"
                link_info = {
                    "url": rec.get("source_url", ""),
                    "title": rec.get("source_title", ""),
                    "source_type": rec.get("source_type", ""),
                    "accessed_date": rec.get("retrieved_at", ""),
                }
                evidence_links.append(link_info)
                source_map.append({
                    "text": excerpt,
                    **link_info,
                })

    if not combined_text.strip():
        return {"_no_content": True}

    extracted: dict = {}
    claim_evidence: list[dict] = []

    # Auth methods — with claim-level evidence
    auth_matches = _search_patterns(combined_text, AUTH_PATTERNS)
    if auth_matches:
        extracted["auth_methods"] = auth_matches
        extracted["auth_methods_status"] = FindingStatus.CONFIRMED_YES.value
        # Build claim evidence for each auth method
        for method in auth_matches:
            patterns = AUTH_PATTERNS.get(method, [])
            for src in source_map:
                for pat in patterns:
                    if re.search(pat, src["text"].lower(), re.IGNORECASE):
                        excerpt = _find_supporting_excerpt(src["text"], pat)
                        claim_evidence.append(ClaimEvidence(
                            claim_field="auth_methods",
                            claim_value=method,
                            source_url=src["url"],
                            source_title=src["title"],
                            supporting_excerpt=excerpt,
                            retrieved_at=src["accessed_date"],
                            confidence=ConfidenceLevel.MEDIUM.value,
                        ).to_dict())
                        break  # one excerpt per source per method

    # API types — with claim-level evidence
    api_matches = _search_patterns(combined_text, API_TYPE_PATTERNS)
    if api_matches:
        extracted["api_type"] = api_matches
        extracted["api_type_status"] = FindingStatus.CONFIRMED_YES.value
        for api_t in api_matches:
            patterns = API_TYPE_PATTERNS.get(api_t, [])
            for src in source_map:
                for pat in patterns:
                    if re.search(pat, src["text"].lower(), re.IGNORECASE):
                        excerpt = _find_supporting_excerpt(src["text"], pat)
                        claim_evidence.append(ClaimEvidence(
                            claim_field="api_type",
                            claim_value=api_t,
                            source_url=src["url"],
                            source_title=src["title"],
                            supporting_excerpt=excerpt,
                            retrieved_at=src["accessed_date"],
                            confidence=ConfidenceLevel.MEDIUM.value,
                        ).to_dict())
                        break

    # Credential accessibility — with claim-level evidence
    cred_matches = _search_patterns(combined_text, CREDENTIAL_PATTERNS)
    if cred_matches:
        # Take the first match (highest priority in dict order)
        extracted["credential_accessibility"] = cred_matches[0]
        extracted["credential_accessibility_status"] = FindingStatus.CONFIRMED_YES.value
        # Evidence for the matched credential type
        patterns = CREDENTIAL_PATTERNS.get(cred_matches[0], [])
        for src in source_map:
            for pat in patterns:
                if re.search(pat, src["text"].lower(), re.IGNORECASE):
                    excerpt = _find_supporting_excerpt(src["text"], pat)
                    claim_evidence.append(ClaimEvidence(
                        claim_field="credential_accessibility",
                        claim_value=cred_matches[0],
                        source_url=src["url"],
                        source_title=src["title"],
                        supporting_excerpt=excerpt,
                        retrieved_at=src["accessed_date"],
                        confidence=ConfidenceLevel.MEDIUM.value,
                    ).to_dict())
                    break

    # MCP detection — with claim-level evidence
    mcp_matches = _search_patterns(combined_text, MCP_PATTERNS)
    if "official_mcp" in mcp_matches:
        extracted["has_official_mcp"] = FindingStatus.CONFIRMED_YES.value
        extracted["_mcp_mentioned"] = True
        mcp_evidence = []
        for src in source_map:
            for pat in MCP_PATTERNS["official_mcp"]:
                if re.search(pat, src["text"].lower(), re.IGNORECASE):
                    mcp_evidence.append({"url": src["url"], "title": src["title"]})
                    break
        extracted["mcp_evidence"] = mcp_evidence
    elif "community_mcp" in mcp_matches:
        extracted["has_community_mcp"] = FindingStatus.CONFIRMED_YES.value
        extracted["_mcp_mentioned"] = True
        mcp_evidence = []
        for src in source_map:
            for pat in MCP_PATTERNS["community_mcp"]:
                if re.search(pat, src["text"].lower(), re.IGNORECASE):
                    mcp_evidence.append({"url": src["url"], "title": src["title"]})
                    break
        extracted["mcp_evidence"] = mcp_evidence
    elif "mcp_mentioned" in mcp_matches:
        extracted["_mcp_mentioned"] = True

    # Evidence
    extracted["evidence_links"] = evidence_links
    extracted["claim_evidence"] = claim_evidence
    extracted["_combined_text"] = combined_text  # for breadth estimation

    return extracted


# ---------------------------------------------------------------------------
# Research pipeline for a single app
# ---------------------------------------------------------------------------


async def research_single_app(
    app: dict,
    category_name: str,
    fetcher: DocumentationFetcher,
    existing_sources: list[dict],
) -> tuple[dict, list[dict]]:
    """
    Research a single application:
    1. Discover candidate sources
    2. Fetch documentation (bounded, fast)
    3. Extract findings via keyword matching
    4. Classify (Prompt 3)
    5. Validate evidence quality (Prompt 3)
    6. Return (finding_dict, source_records)
    """
    app_id = app["id"]
    app_name = app["name"]
    t_start = time.monotonic()
    print(f"\n[{app_id}] Investigating {app_name} ({category_name})...", flush=True)

    # Discover sources
    candidate_records = discover_all_candidate_sources(app_id, app_name)

    # Filter out already-fetched sources
    existing_urls = {r.get("source_url") for r in existing_sources if r.get("app_id") == app_id}
    new_records = [r for r in candidate_records if r.source_url not in existing_urls]

    # Prioritize known docs (max 3). If none known, try at most 2 candidate URLs.
    known = [r for r in new_records if r.discovery_method == "known_docs_map"]
    if known:
        to_fetch = known[:3]
    else:
        to_fetch = [r for r in new_records if r.discovery_method != "known_docs_map"][:2]

    print(f"  Attempting to fetch {len(to_fetch)} source(s)...", flush=True)
    for s in to_fetch:
        print(f"    -> {s.source_url} [{s.source_type}]", flush=True)

    # Fetch with timeout
    if to_fetch:
        try:
            await asyncio.wait_for(fetcher.fetch_sources(to_fetch), timeout=25.0)
        except asyncio.TimeoutError:
            print(f"  ⚠️ Fetch timed out after 25s for {app_name}, proceeding with available data.", flush=True)

    # Build complete source records for this app
    all_app_sources = [r.to_dict() for r in to_fetch]
    for rec in existing_sources:
        if rec.get("app_id") == app_id:
            all_app_sources.append(rec)

    # Extract findings
    extracted = extract_from_content(all_app_sources)

    # Build finding
    finding = create_empty_finding(
        app_id=app_id,
        app_name=app_name,
        category_id=app.get("category_id", 0),
        category_name=category_name,
    )
    result = finding.to_dict()

    # Apply extracted fields
    if not extracted.get("_no_content"):
        for key in [
            "auth_methods", "auth_methods_status",
            "api_type", "api_type_status",
            "credential_accessibility", "credential_accessibility_status",
            "evidence_links", "claim_evidence",
            "has_official_mcp", "has_community_mcp",
            "_mcp_mentioned", "mcp_evidence",
        ]:
            if key in extracted:
                result[key] = extracted[key]

        if extracted.get("auth_methods") or extracted.get("api_type"):
            result["overall_confidence"] = ConfidenceLevel.MEDIUM.value
        else:
            result["overall_confidence"] = ConfidenceLevel.LOW.value
    else:
        result["overall_confidence"] = ConfidenceLevel.LOW.value
        result["research_notes"] = "No documentation content could be fetched."

    # --- Prompt 3: Classification ---
    combined_text = extracted.get("_combined_text", "")
    classification = classify_app(result, combined_text)
    for k, v in classification.items():
        result[k] = v

    # --- Prompt 3: Evidence quality validation ---
    eq = validate_evidence_quality(result)
    result["evidence_quality_score"] = eq["quality_score"]
    result["evidence_warnings"] = eq["warnings"]

    # Clean up internal fields
    result.pop("_mcp_mentioned", None)
    result.pop("mcp_evidence", None)

    # Timing
    elapsed = time.monotonic() - t_start
    result["research_duration_seconds"] = round(elapsed, 2)
    result["researched_at"] = datetime.now(timezone.utc).isoformat()

    success_count = sum(1 for r in all_app_sources if r.get("fetch_status") == FetchStatus.SUCCESS.value)
    fail_count = sum(1 for r in all_app_sources if r.get("fetch_status") == FetchStatus.FAILED.value)
    blocked_count = sum(1 for r in all_app_sources if r.get("fetch_status") in (FetchStatus.BLOCKED.value, FetchStatus.RATE_LIMITED.value))

    print(
        f"  Result: {success_count} succeeded, {fail_count} failed, {blocked_count} blocked/rate-limited.\n"
        f"  Auth: {result.get('auth_methods', [])} | API: {result.get('api_type', [])} | Confidence: {result.get('overall_confidence')}\n"
        f"  Breadth: {result.get('api_breadth')} | MCP: {result.get('mcp_status')} | Buildability: {result.get('buildability_verdict')} (score={result.get('toolkit_buildability_score')})\n"
        f"  Duration: {elapsed:.2f}s",
        flush=True
    )

    return result, [r.to_dict() for r in to_fetch]


# ---------------------------------------------------------------------------
# Batch research
# ---------------------------------------------------------------------------


async def research_apps(
    app_ids: Optional[list[int]] = None,
    category_name: Optional[str] = None,
    limit: Optional[int] = None,
    skip_completed: bool = True,
    concurrency: int = 5,
) -> dict:
    """
    Research multiple applications.

    Args:
        app_ids: Specific app IDs to research. None = all.
        category_name: Filter by category name.
        limit: Max number of apps to research.
        skip_completed: Skip apps already researched.
        concurrency: Max concurrent HTTP requests.

    Returns:
        Summary dict with counts and any errors.
    """
    apps_data = load_apps()
    categories = {c["id"]: c["name"] for c in apps_data["categories"]}
    all_apps = apps_data["applications"]

    # Filter apps
    if app_ids:
        target_apps = [a for a in all_apps if a["id"] in app_ids]
    elif category_name:
        cat_id = None
        for c in apps_data["categories"]:
            if c["name"].lower() == category_name.lower():
                cat_id = c["id"]
                break
        if cat_id is None:
            return {"error": f"Category not found: {category_name}"}
        target_apps = [a for a in all_apps if a["category_id"] == cat_id]
    else:
        target_apps = list(all_apps)

    # Load existing state
    results = get_or_initialize_results()
    results_by_id = {r["app_id"]: r for r in results}
    existing_sources = load_source_records()

    # Skip completed if requested
    if skip_completed:
        target_apps = [
            a for a in target_apps
            if results_by_id.get(a["id"], {}).get("overall_confidence")
            == ConfidenceLevel.UNVERIFIED.value
        ]

    # Apply limit
    if limit is not None:
        target_apps = target_apps[:limit]

    if not target_apps:
        return {"researched": 0, "message": "No apps to research (all complete or none match filter)."}

    logger.info(f"Researching {len(target_apps)} applications (concurrency={concurrency})...")

    fetcher = DocumentationFetcher(concurrency=concurrency)
    new_sources: list[dict] = []
    errors: list[str] = []
    researched_count = 0

    # Save first-pass state before we start (for traceability)
    first_pass = load_first_pass()
    if not first_pass:
        first_pass = list(results)

    for app in target_apps:
        cat_name = categories.get(app["category_id"], "Unknown")
        try:
            finding, sources = await research_single_app(
                app, cat_name, fetcher, existing_sources
            )
            # Update result
            results_by_id[app["id"]] = finding
            new_sources.extend(sources)
            researched_count += 1

            # Save intermediate results after each app
            results = [results_by_id.get(a["id"], {}) for a in all_apps if a["id"] in results_by_id]
            save_results(results)

        except Exception as e:
            err_msg = f"Error researching {app['name']} (id={app['id']}): {e}"
            logger.error(err_msg)
            errors.append(err_msg)

    # Save all source records
    merged_sources = merge_source_records(existing_sources, new_sources)
    save_source_records(merged_sources)

    # Save first-pass (only on first run)
    if not load_first_pass():
        save_first_pass(results)

    # Final save
    final_results = [results_by_id.get(a["id"], {}) for a in all_apps if a["id"] in results_by_id]
    save_results(final_results)

    # Export CSV
    export_csv(final_results)

    summary = {
        "researched": researched_count,
        "total_sources_discovered": len(new_sources),
        "total_sources_stored": len(merged_sources),
        "errors": errors,
        "progress": get_research_progress(),
    }
    logger.info(f"Research complete: {json.dumps(summary, indent=2)}")
    return summary


if __name__ == "__main__":
    from .__main__ import main
    main()
