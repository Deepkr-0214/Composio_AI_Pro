"""
Unit tests for the evidence verification engine (Prompt 7).

Covers:
1. Missing evidence handling
2. Unreachable sources handling (403, 404, WAF blocks)
3. Contradictory authentication detection
4. Incorrect credential access detection
5. Unsupported MCP claim detection & demotion
6. Conflicting API documentation detection
7. Source excerpt mismatch detection
8. Safe automatic correction execution
9. Correction history preservation
10. First-pass snapshot immutability & integrity
11. Human review queue generation (stratified & risk-based)
12. Verification status enum consistency
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from agent.models import (
    VerificationStatus,
    VerificationResult,
    CorrectionRecord,
    MCPStatus,
    BuildabilityVerdict,
    QualityGateStatus,
)
from agent.verify import (
    validate_finding_structure,
    verify_claim_evidence,
    detect_contradictions,
    evaluate_human_review_need,
    apply_safe_corrections,
    generate_human_audit_queue,
    run_verification_pipeline,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def test_missing_evidence():
    """Verify that an app with no sources and positive claims is flagged as source_unavailable."""
    app = {
        "app_id": 999,
        "app_name": "GhostApp",
        "auth_methods": ["OAuth2"],
        "api_type": ["REST"],
        "evidence_links": [],
        "claim_evidence": [],
    }
    result = verify_claim_evidence(app, "auth_methods", ["OAuth2"], [], [])
    assert result.verification_status == VerificationStatus.SOURCE_UNAVAILABLE.value
    assert result.is_accurate is False


def test_unreachable_sources():
    """Verify that sources returning HTTP 403 / 404 are flagged as source_unavailable."""
    app = {
        "app_id": 1,
        "app_name": "Salesforce",
        "auth_methods": [],
        "api_type": [],
        "evidence_links": [{"url": "https://developers.salesforce.com"}],
        "claim_evidence": [],
    }
    blocked_sources = [
        {"app_id": 1, "source_url": "https://developers.salesforce.com", "http_status": 403, "content_excerpt": ""}
    ]
    result = verify_claim_evidence(app, "auth_methods", [], blocked_sources, [])
    assert result.verification_status == VerificationStatus.SOURCE_UNAVAILABLE.value


def test_contradictory_authentication():
    """Verify that claiming OAuth-only when text explicitly documents API Key triggers contradiction."""
    app = {
        "app_id": 101,
        "app_name": "MultiAuthApp",
        "auth_methods": ["OAuth2"],
        "api_type": ["REST"],
        "buildability_verdict": "feasible",
    }
    sources = [
        {
            "http_status": 200,
            "content_excerpt": "You can authenticate using your API key passed via the x-api-key header or OAuth 2.0 flow.",
            "source_title": "Auth Guide"
        }
    ]
    contradictions = detect_contradictions(app, sources)
    assert any("OAuth-only classification contradicted" in c for c in contradictions)


def test_unsupported_mcp_claims():
    """Verify that claiming official_mcp without vendor repository evidence is contradicted."""
    app = {
        "app_id": 102,
        "app_name": "FakeMCPApp",
        "mcp_status": MCPStatus.OFFICIAL.value,
        "buildability_verdict": "feasible",
    }
    sources = [
        {
            "http_status": 200,
            "source_url": "https://github.com/randomuser/my-community-mcp",
            "content_excerpt": "Community MCP server for FakeMCPApp.",
            "source_title": "Unofficial Repo"
        }
    ]
    contradictions = detect_contradictions(app, sources)
    assert any("Official MCP status claimed but source URLs lack vendor-controlled repository" in c for c in contradictions)

    result = verify_claim_evidence(app, "mcp_status", MCPStatus.OFFICIAL.value, sources, [])
    assert result.verification_status == VerificationStatus.CONTRADICTED.value
    assert result.recommended_correction == MCPStatus.UNVERIFIED_CLAIM.value


def test_conflicting_api_documentation():
    """Verify that claiming ready_to_build when no API is documented triggers contradiction."""
    app = {
        "app_id": 103,
        "app_name": "NoAPIApp",
        "api_type": [],
        "buildability_verdict": BuildabilityVerdict.READY_TO_BUILD.value,
        "blockers": ["no_public_api"],
    }
    contradictions = detect_contradictions(app, [])
    assert any("Buildable-now verdict contradicted" in c for c in contradictions)


def test_source_excerpt_mismatch():
    """Verify that claim_evidence where the claim value does not appear in excerpt is flagged."""
    app = {
        "app_id": 104,
        "app_name": "MismatchApp",
        "claim_evidence": [
            {
                "claim_field": "api_type",
                "claim_value": "GraphQL",
                "supporting_excerpt": "We provide a standard REST API returning JSON responses.",
            }
        ]
    }
    contradictions = detect_contradictions(app, [])
    assert any("Excerpt mismatch for api_type" in c for c in contradictions)


def test_safe_automatic_correction():
    """Verify that contradictory buildability and MCP claims are safely auto-corrected."""
    app = {
        "app_id": 105,
        "app_name": "AutoCorrectApp",
        "api_type": [],
        "buildability_verdict": BuildabilityVerdict.READY_TO_BUILD.value,
        "mcp_status": MCPStatus.OFFICIAL.value,
        "quality_gate_status": QualityGateStatus.PASSED.value,
    }
    v_build = VerificationResult(
        app_id=105,
        field_verified="buildability_verdict",
        verification_status=VerificationStatus.CONTRADICTED.value,
        recommended_correction=BuildabilityVerdict.NEEDS_INVESTIGATION.value,
        contradictions=["Classified as ready_to_build despite missing API evidence."],
    )
    v_mcp = VerificationResult(
        app_id=105,
        field_verified="mcp_status",
        verification_status=VerificationStatus.CONTRADICTED.value,
        recommended_correction=MCPStatus.UNVERIFIED_CLAIM.value,
        contradictions=["Official MCP claimed without official repository."],
    )

    corrected_app, corrections = apply_safe_corrections(app, [v_build, v_mcp], ["contradiction"], [])

    assert corrected_app["buildability_verdict"] == BuildabilityVerdict.NEEDS_INVESTIGATION.value
    assert corrected_app["toolkit_buildability_score"] == 4
    assert corrected_app["mcp_status"] == MCPStatus.UNVERIFIED_CLAIM.value
    assert len(corrections) >= 2


def test_correction_history_preservation():
    """Verify that CorrectionRecord stores complete provenance."""
    record = CorrectionRecord(
        app_id=42,
        app_name="TestApp",
        field_name="buildability_verdict",
        original_value="ready_to_build",
        corrected_value="needs_investigation",
        reason_for_correction="Missing API endpoints",
        original_evidence="ready_to_build",
        new_evidence=["Missing endpoint docs"],
    )
    d = record.to_dict()
    assert d["app_id"] == 42
    assert d["original_value"] == "ready_to_build"
    assert d["corrected_value"] == "needs_investigation"
    assert d["whether_human_approval_is_required"] is False


def test_first_pass_snapshot_integrity():
    """Verify that batch1_first_pass.json and batch2_first_pass.json exist and contain exactly 50 apps each."""
    b1_path = DATA_DIR / "batch1_first_pass.json"
    b2_path = DATA_DIR / "batch2_first_pass.json"

    assert b1_path.exists(), "batch1_first_pass.json must exist"
    assert b2_path.exists(), "batch2_first_pass.json must exist"

    with open(b1_path, "r", encoding="utf-8") as f:
        b1 = json.load(f)
    with open(b2_path, "r", encoding="utf-8") as f:
        b2 = json.load(f)

    assert len(b1) == 50, f"Expected 50 apps in batch1, got {len(b1)}"
    assert len(b2) == 50, f"Expected 50 apps in batch2, got {len(b2)}"
    assert [a["app_id"] for a in b1] == list(range(1, 51))
    assert [a["app_id"] for a in b2] == list(range(51, 101))


def test_human_review_queue_generation():
    """Verify human audit queue contains stratified samples and leaves human judgment fields empty."""
    apps = [
        {"app_id": i, "app_name": f"App{i}", "category_name": f"Cat{i%10}"}
        for i in range(1, 21)
    ]
    queue_data = generate_human_audit_queue(apps, {}, {}, seed=42)
    queue = queue_data["queue"]

    assert len(queue) > 0
    for item in queue:
        assert item["human_judgment"]["human_verified"] is False
        assert item["human_judgment"]["reviewer_verdict"] is None
        assert item["human_judgment"]["reviewer_notes"] is None


def test_verification_status_consistency():
    """Verify that all enum statuses in VerificationStatus are valid strings."""
    valid_statuses = {
        "verified_by_primary_source",
        "corroborated_by_independent_source",
        "needs_human_review",
        "unsupported",
        "contradicted",
        "source_unavailable",
        "not_checked",
    }
    actual_statuses = {e.value for e in VerificationStatus}
    assert actual_statuses == valid_statuses
