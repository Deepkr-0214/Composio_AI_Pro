"""
Automated tests for the Composio research agent.

Tests cover:
- Dataset loading and validation
- Source record creation and validation
- URL normalization and candidate generation
- Duplicate source prevention
- Evidence serialization
- Research resume behavior
- Content extraction
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.models import (
    ResearchFinding,
    FindingStatus,
    ConfidenceLevel,
    APIBreadth,
    CredentialAccessibility,
    MCPStatus,
    BuildabilityVerdict,
    BlockerType,
    QualityGateStatus,
    ClaimEvidence,
    create_empty_finding,
)
from agent.sources import (
    SourceRecord,
    FetchStatus,
    SourceType,
    discover_known_sources,
    discover_all_candidate_sources,
    build_candidate_urls,
    build_mcp_search_urls,
    merge_source_records,
    content_hash,
    _normalize_app_key,
)
from agent.fetcher import check_content_validity
from agent.research import (
    load_apps,
    extract_from_content,
    get_or_initialize_results,
    calculate_pilot_metrics,
    save_pilot_first_pass,
    PILOT_APP_IDS,
)
from agent.classify import (
    classify_integration_readiness,
    IntegrationTier,
    assess_buildability,
    estimate_api_breadth,
    classify_mcp_status,
    classify_app,
    validate_evidence_quality,
    evaluate_quality_gates,
    get_category_summary,
)


# ---------------------------------------------------------------------------
# Dataset tests
# ---------------------------------------------------------------------------


class TestDatasetLoading:
    """Tests for loading and validating the apps dataset."""

    def test_load_apps_returns_dict(self):
        data = load_apps()
        assert isinstance(data, dict)

    def test_apps_has_100_entries(self):
        data = load_apps()
        assert len(data["applications"]) == 100

    def test_apps_has_10_categories(self):
        data = load_apps()
        assert len(data["categories"]) == 10

    def test_all_app_ids_unique(self):
        data = load_apps()
        ids = [a["id"] for a in data["applications"]]
        assert len(ids) == len(set(ids))

    def test_all_app_names_unique(self):
        data = load_apps()
        names = [a["name"] for a in data["applications"]]
        assert len(names) == len(set(names))

    def test_all_apps_have_valid_category(self):
        data = load_apps()
        cat_ids = {c["id"] for c in data["categories"]}
        for app in data["applications"]:
            assert app["category_id"] in cat_ids, f"App {app['name']} has invalid category"

    def test_sequential_ids(self):
        data = load_apps()
        ids = sorted(a["id"] for a in data["applications"])
        assert ids == list(range(1, 101))

    def test_no_empty_names(self):
        data = load_apps()
        for app in data["applications"]:
            assert app["name"].strip(), f"App id={app['id']} has empty name"


# ---------------------------------------------------------------------------
# Source record tests
# ---------------------------------------------------------------------------


class TestSourceRecords:
    """Tests for source record creation and validation."""

    def test_source_record_creation(self):
        rec = SourceRecord(
            app_id=1,
            app_name="Salesforce",
            source_type=SourceType.API_REFERENCE.value,
            source_url="https://developer.salesforce.com/docs/apis",
            discovery_method="known_docs_map",
        )
        assert rec.app_id == 1
        assert rec.fetch_status == FetchStatus.PENDING.value

    def test_source_record_to_dict(self):
        rec = SourceRecord(app_id=1, app_name="Test", source_type="api_reference")
        d = rec.to_dict()
        assert isinstance(d, dict)
        assert d["app_id"] == 1
        assert "fetch_status" in d

    def test_source_record_from_dict(self):
        d = {
            "app_id": 1,
            "app_name": "Test",
            "source_type": "api_reference",
            "fetch_status": "success",
            "source_url": "https://example.com",
        }
        rec = SourceRecord.from_dict(d)
        assert rec.app_id == 1
        assert rec.fetch_status == "success"

    def test_source_record_default_values(self):
        rec = SourceRecord(app_id=1, app_name="Test", source_type="api_reference")
        assert rec.source_url is None
        assert rec.final_url is None
        assert rec.http_status is None
        assert rec.content_excerpt is None
        assert rec.fetch_status == FetchStatus.PENDING.value


# ---------------------------------------------------------------------------
# URL normalization and candidate generation
# ---------------------------------------------------------------------------


class TestURLGeneration:
    """Tests for URL candidate generation."""

    def test_normalize_app_key(self):
        assert _normalize_app_key("HubSpot") == "hubspot"
        assert _normalize_app_key("  Salesforce  ") == "salesforce"
        assert _normalize_app_key("Zoho CRM") == "zoho crm"

    def test_known_sources_for_github(self):
        sources = discover_known_sources(61, "GitHub")
        assert len(sources) >= 1
        urls = [s.source_url for s in sources]
        assert any("github.com" in u for u in urls if u)

    def test_known_sources_for_unknown_app(self):
        sources = discover_known_sources(999, "NonexistentApp123")
        assert len(sources) == 0

    def test_candidate_urls_not_empty(self):
        candidates = build_candidate_urls("Stripe")
        assert len(candidates) > 0

    def test_candidate_urls_no_duplicates(self):
        candidates = build_candidate_urls("HubSpot")
        urls = [c["url"] for c in candidates]
        assert len(urls) == len(set(urls))

    def test_mcp_search_urls(self):
        urls = build_mcp_search_urls("Notion")
        assert len(urls) >= 1
        assert any("mcp" in u["url"] for u in urls)

    def test_all_candidate_sources_no_duplicates(self):
        sources = discover_all_candidate_sources(81, "Stripe")
        urls = [s.source_url for s in sources if s.source_url]
        assert len(urls) == len(set(urls)), "Duplicate URLs in candidate sources"


# ---------------------------------------------------------------------------
# Duplicate prevention
# ---------------------------------------------------------------------------


class TestDuplicatePrevention:
    """Tests for preventing duplicate source records."""

    def test_merge_no_duplicates(self):
        existing = [
            {"app_id": 1, "source_url": "https://a.com"},
            {"app_id": 2, "source_url": "https://b.com"},
        ]
        new = [
            {"app_id": 1, "source_url": "https://a.com"},  # duplicate
            {"app_id": 3, "source_url": "https://c.com"},  # new
        ]
        merged = merge_source_records(existing, new)
        assert len(merged) == 3
        urls = [(r["app_id"], r["source_url"]) for r in merged]
        assert len(urls) == len(set(urls))

    def test_merge_empty_existing(self):
        merged = merge_source_records([], [{"app_id": 1, "source_url": "https://a.com"}])
        assert len(merged) == 1

    def test_merge_empty_new(self):
        existing = [{"app_id": 1, "source_url": "https://a.com"}]
        merged = merge_source_records(existing, [])
        assert len(merged) == 1


# ---------------------------------------------------------------------------
# Content extraction tests
# ---------------------------------------------------------------------------


class TestContentExtraction:
    """Tests for keyword-based content extraction."""

    def test_extract_auth_methods(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "Use OAuth2 to authenticate. You can also use API Key for simple access.",
            "source_url": "https://example.com",
            "source_title": "Auth Docs",
            "source_type": "api_reference",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert "OAuth2" in result.get("auth_methods", [])
        assert "API Key" in result.get("auth_methods", [])

    def test_extract_api_types(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "Our REST API supports CRUD operations. We also offer a GraphQL endpoint.",
            "source_url": "https://example.com",
            "source_title": "API Docs",
            "source_type": "api_reference",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert "REST" in result.get("api_type", [])
        assert "GraphQL" in result.get("api_type", [])

    def test_extract_no_content(self):
        records = [{"fetch_status": "failed", "content_excerpt": ""}]
        result = extract_from_content(records)
        assert result.get("_no_content") is True

    def test_extract_evidence_links_populated(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "REST API available with API Key authentication.",
            "source_url": "https://example.com/api",
            "source_title": "API Reference",
            "source_type": "api_reference",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert len(result.get("evidence_links", [])) >= 1
        assert result["evidence_links"][0]["url"] == "https://example.com/api"

    def test_extract_credential_accessibility(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "Sign up for free tier to get your API key. No credit card required.",
            "source_url": "https://example.com",
            "source_title": "Getting Started",
            "source_type": "official_documentation",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert result.get("credential_accessibility") == "free_self_serve"


# ---------------------------------------------------------------------------
# Content hash
# ---------------------------------------------------------------------------


class TestContentHash:
    def test_hash_deterministic(self):
        assert content_hash("hello") == content_hash("hello")

    def test_hash_different_for_different_content(self):
        assert content_hash("hello") != content_hash("world")

    def test_hash_length(self):
        assert len(content_hash("test")) == 16


# ---------------------------------------------------------------------------
# Evidence serialization
# ---------------------------------------------------------------------------


class TestEvidenceSerialization:
    """Tests for research finding serialization."""

    def test_finding_to_dict(self):
        finding = create_empty_finding(1, "Test", 1, "CRM")
        d = finding.to_dict()
        assert isinstance(d, dict)
        assert d["app_id"] == 1
        assert d["auth_methods_status"] == FindingStatus.UNKNOWN.value

    def test_finding_roundtrip(self):
        finding = create_empty_finding(1, "Test", 1, "CRM")
        d = finding.to_dict()
        restored = ResearchFinding.from_dict(d)
        assert restored.app_id == finding.app_id
        assert restored.app_name == finding.app_name

    def test_finding_json_serializable(self):
        finding = create_empty_finding(1, "Test", 1, "CRM")
        d = finding.to_dict()
        serialized = json.dumps(d)
        assert isinstance(serialized, str)
        deserialized = json.loads(serialized)
        assert deserialized["app_id"] == 1


# ---------------------------------------------------------------------------
# Classification tests
# ---------------------------------------------------------------------------


class TestClassification:
    def test_unverified_is_unknown(self):
        f = {"overall_confidence": "unverified"}
        assert classify_integration_readiness(f) == IntegrationTier.UNKNOWN

    def test_blocked_by_no_api(self):
        f = {"overall_confidence": "medium", "api_type_status": "confirmed_no"}
        assert classify_integration_readiness(f) == IntegrationTier.BLOCKED

    def test_ready_tier(self):
        f = {
            "overall_confidence": "high",
            "api_breadth": "comprehensive",
            "credential_accessibility": "free_self_serve",
        }
        assert classify_integration_readiness(f) == IntegrationTier.READY


# ---------------------------------------------------------------------------
# Resume behavior
# ---------------------------------------------------------------------------


class TestResumeBehavior:
    """Test that research can resume from previous state."""

    def test_get_or_initialize_creates_results(self):
        results = get_or_initialize_results()
        assert isinstance(results, list)
        # Should have entries (100 if apps.json is loaded)
        assert len(results) > 0

    def test_results_all_start_unverified(self):
        apps_data = load_apps()
        categories = {c["id"]: c["name"] for c in apps_data["categories"]}
        for app in apps_data["applications"]:
            f = create_empty_finding(
                app_id=app["id"],
                app_name=app["name"],
                category_id=app["category_id"],
                category_name=categories[app["category_id"]],
            )
            assert f.overall_confidence == ConfidenceLevel.UNVERIFIED.value


# ---------------------------------------------------------------------------
# Prompt 3: Authentication and API Protocol Extraction Tests
# ---------------------------------------------------------------------------


class TestPrompt3AuthAndAPIExtraction:
    """Tests for multi-auth, unknown preservation, and protocol extraction."""

    def test_multi_auth_detection(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": (
                "Authenticate using OAuth2 authorization code flow. "
                "Alternatively, you may pass an API Key via x-api-key header "
                "or generate a Personal Access Token in your account settings."
            ),
            "source_url": "https://api.example.com/docs/auth",
            "source_title": "Authentication Guide",
            "source_type": "authentication_documentation",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        methods = result.get("auth_methods", [])
        assert "OAuth2" in methods
        assert "API Key" in methods
        assert "Personal Access Token" in methods
        assert len(methods) >= 3

    def test_unknown_auth_preserved(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "Welcome to our documentation. Learn how to configure your settings and profile.",
            "source_url": "https://docs.example.com",
            "source_title": "Overview",
            "source_type": "official_documentation",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert "auth_methods" not in result
        assert result.get("auth_methods_status") is None

    def test_service_account_and_jwt(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "Server-to-server calls require a Service Account key signed as a JWT bearer token.",
            "source_url": "https://docs.example.com/service-accounts",
            "source_title": "Service Accounts",
            "source_type": "authentication_documentation",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        methods = result.get("auth_methods", [])
        assert "Service Account" in methods
        assert "JWT" in methods

    def test_multi_api_protocols(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": (
                "Our platform offers a REST API for standard operations, "
                "a GraphQL endpoint for flexible querying, and Webhook subscriptions for real-time events."
            ),
            "source_url": "https://docs.example.com/api",
            "source_title": "API Overview",
            "source_type": "api_reference",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        types = result.get("api_type", [])
        assert "REST" in types
        assert "GraphQL" in types
        assert "Webhook" in types

    def test_claim_level_evidence_created(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "Use OAuth2 to authenticate your requests against the REST API.",
            "source_url": "https://api.example.com/docs",
            "source_title": "API Reference",
            "source_type": "api_reference",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        claim_ev = result.get("claim_evidence", [])
        assert len(claim_ev) >= 2  # At least one for auth, one for api_type
        auth_claims = [c for c in claim_ev if c["claim_field"] == "auth_methods"]
        assert len(auth_claims) >= 1
        assert auth_claims[0]["claim_value"] == "OAuth2"
        assert auth_claims[0]["source_url"] == "https://api.example.com/docs"
        assert auth_claims[0]["supporting_excerpt"] != ""


# ---------------------------------------------------------------------------
# Prompt 3: Credential Accessibility Tests
# ---------------------------------------------------------------------------


class TestPrompt3CredentialAccessibility:
    """Tests for free self-serve, paid, trial, partner, and enterprise tiers."""

    def test_free_self_serve(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "Sign up for free and get instant API key access. No credit card required.",
            "source_url": "https://example.com/signup",
            "source_title": "Sign Up",
            "source_type": "official_documentation",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert result.get("credential_accessibility") == CredentialAccessibility.FREE_SELF_SERVE.value

    def test_trial_self_serve(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "Start your 14-day free trial today. Try for free with full API access.",
            "source_url": "https://example.com/pricing",
            "source_title": "Pricing",
            "source_type": "official_documentation",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert result.get("credential_accessibility") == CredentialAccessibility.TRIAL_SELF_SERVE.value

    def test_paid_self_serve(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "API access requires a paid plan. View our subscription required tiers.",
            "source_url": "https://example.com/pricing",
            "source_title": "Pricing",
            "source_type": "official_documentation",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert result.get("credential_accessibility") == CredentialAccessibility.PAID_SELF_SERVE.value

    def test_partner_approval(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "API access is available through our partner program only. Partner access approval required.",
            "source_url": "https://example.com/partners",
            "source_title": "Partner Program",
            "source_type": "official_documentation",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert result.get("credential_accessibility") == CredentialAccessibility.PARTNER_APPROVAL.value

    def test_contact_sales(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "Contact sales for API access and enterprise deployment options.",
            "source_url": "https://example.com/contact",
            "source_title": "Contact",
            "source_type": "official_documentation",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert result.get("credential_accessibility") in (
            CredentialAccessibility.CONTACT_SALES.value,
            CredentialAccessibility.ENTERPRISE_ONLY.value,
        )

    def test_enterprise_only(self):
        records = [{
            "fetch_status": "success",
            "content_excerpt": "Enterprise plan only. Requires dedicated contract and custom enterprise license.",
            "source_url": "https://example.com/enterprise",
            "source_title": "Enterprise",
            "source_type": "official_documentation",
            "retrieved_at": "2026-01-01T00:00:00Z",
        }]
        result = extract_from_content(records)
        assert result.get("credential_accessibility") == CredentialAccessibility.ENTERPRISE_ONLY.value


# ---------------------------------------------------------------------------
# Prompt 3: API Breadth and MCP Support Tests
# ---------------------------------------------------------------------------


class TestPrompt3BreadthAndMCP:
    """Tests for API breadth estimation and MCP status classification."""

    def test_estimate_api_breadth_extensive(self):
        rich_text = (
            "Our API allows you to create, read, update, delete, and list resources. "
            "Manage users, contacts, accounts, orders, products, tickets, invoices, workflows, "
            "events, files, messages, channels, webhooks, and pipelines. "
            "Features include bulk operations, batch processing, pagination, rate limit headers, "
            "and search filters."
        )
        res = estimate_api_breadth(rich_text)
        assert res["breadth"] == APIBreadth.EXTENSIVE.value
        assert "Extensive" in res["justification"]

    def test_estimate_api_breadth_narrow(self):
        sparse_text = "The API allows you to create a ping event."
        res = estimate_api_breadth(sparse_text)
        assert res["breadth"] == APIBreadth.NARROW.value

    def test_estimate_api_breadth_unknown(self):
        res = estimate_api_breadth("")
        assert res["breadth"] == APIBreadth.UNKNOWN.value

    def test_mcp_official_classification(self):
        finding = {
            "has_official_mcp": FindingStatus.CONFIRMED_YES.value,
            "mcp_evidence": [{"url": "https://github.com/example/official-mcp", "title": "Repo"}],
        }
        res = classify_mcp_status(finding)
        assert res["mcp_status"] == MCPStatus.OFFICIAL.value
        assert res["mcp_repo_url"] == "https://github.com/example/official-mcp"

    def test_mcp_community_classification(self):
        finding = {
            "has_community_mcp": FindingStatus.CONFIRMED_YES.value,
            "mcp_evidence": [{"url": "https://github.com/community/mcp-server", "title": "Repo"}],
        }
        res = classify_mcp_status(finding)
        assert res["mcp_status"] == MCPStatus.COMMUNITY.value
        assert "community" in res["mcp_repo_url"]

    def test_mcp_unverified_claim(self):
        finding = {
            "_mcp_mentioned": True,
            "has_official_mcp": FindingStatus.UNKNOWN.value,
            "has_community_mcp": FindingStatus.UNKNOWN.value,
        }
        res = classify_mcp_status(finding)
        assert res["mcp_status"] == MCPStatus.UNVERIFIED_CLAIM.value

    def test_mcp_unknown(self):
        finding = {}
        res = classify_mcp_status(finding)
        assert res["mcp_status"] == MCPStatus.UNKNOWN.value


# ---------------------------------------------------------------------------
# Prompt 3: Buildability Assessment Tests
# ---------------------------------------------------------------------------


class TestPrompt3BuildabilityAssessment:
    """Tests for buildability scoring, verdicts, and blocker identification."""

    def test_buildability_ready_to_build(self):
        finding = {
            "api_type": ["REST", "GraphQL"],
            "api_type_status": FindingStatus.CONFIRMED_YES.value,
            "auth_methods": ["OAuth2", "API Key"],
            "credential_accessibility": CredentialAccessibility.FREE_SELF_SERVE.value,
            "api_breadth": APIBreadth.BROAD.value,
            "mcp_status": MCPStatus.OFFICIAL.value,
        }
        result = assess_buildability(finding)
        assert result["verdict"] == BuildabilityVerdict.READY_TO_BUILD.value
        assert result["score"] >= 8
        assert not result["blockers"]

    def test_buildability_blocked_by_no_public_api(self):
        finding = {
            "api_type_status": FindingStatus.CONFIRMED_NO.value,
            "credential_accessibility": CredentialAccessibility.UNKNOWN.value,
        }
        result = assess_buildability(finding)
        assert result["verdict"] == BuildabilityVerdict.NOT_FEASIBLE.value
        assert BlockerType.NO_PUBLIC_API.value in result["blockers"]

    def test_buildability_significant_barriers_partner_access(self):
        finding = {
            "api_type": ["REST"],
            "api_type_status": FindingStatus.CONFIRMED_YES.value,
            "auth_methods": ["OAuth2"],
            "credential_accessibility": CredentialAccessibility.PARTNER_APPROVAL.value,
            "api_breadth": APIBreadth.NARROW.value,
        }
        result = assess_buildability(finding)
        assert BlockerType.CREDENTIAL_BARRIER.value in result["blockers"]
        assert result["score"] < 8


# ---------------------------------------------------------------------------
# Prompt 3: Evidence Quality Validation Tests
# ---------------------------------------------------------------------------


class TestPrompt3EvidenceQuality:
    """Tests for quality checks, missing URLs, contradictions, and MCP validation."""

    def test_evidence_quality_flags_missing_links(self):
        finding = {
            "app_name": "TestApp",
            "evidence_links": [],
            "overall_confidence": ConfidenceLevel.LOW.value,
        }
        res = validate_evidence_quality(finding)
        assert any("No evidence links" in w for w in res["warnings"])
        assert res["quality_score"] < 1.0

    def test_evidence_quality_flags_mcp_without_repo(self):
        finding = {
            "app_name": "TestApp",
            "evidence_links": [{"url": "https://docs.example.com", "title": "Docs"}],
            "mcp_status": MCPStatus.OFFICIAL.value,
            "mcp_repo_url": "",
            "overall_confidence": ConfidenceLevel.HIGH.value,
        }
        res = validate_evidence_quality(finding)
        assert any("no repository URL recorded" in w for w in res["warnings"])

    def test_evidence_quality_flags_ready_without_api(self):
        finding = {
            "app_name": "TestApp",
            "evidence_links": [{"url": "https://docs.example.com", "title": "Docs"}],
            "buildability_verdict": BuildabilityVerdict.READY_TO_BUILD.value,
            "api_type_status": FindingStatus.UNKNOWN.value,
            "overall_confidence": ConfidenceLevel.MEDIUM.value,
        }
        res = validate_evidence_quality(finding)
        assert any("API status is unknown" in w for w in res["warnings"])

    def test_evidence_quality_high_score_for_complete_finding(self):
        finding = {
            "app_name": "TestApp",
            "evidence_links": [{"url": "https://docs.example.com", "title": "Docs"}],
            "auth_methods": ["API Key"],
            "credential_accessibility": CredentialAccessibility.FREE_SELF_SERVE.value,
            "api_type_status": FindingStatus.CONFIRMED_YES.value,
            "buildability_verdict": BuildabilityVerdict.READY_TO_BUILD.value,
            "overall_confidence": ConfidenceLevel.HIGH.value,
        }
        res = validate_evidence_quality(finding)
        assert res["quality_score"] >= 0.8
        assert not res["has_critical_gaps"]


# ---------------------------------------------------------------------------
# Prompt 3: Full App Classification Integration Tests
# ---------------------------------------------------------------------------


class TestPrompt3ClassifyAppIntegration:
    """Tests for classify_app orchestration and category summary."""

    def test_classify_app_enriches_finding(self):
        finding = {
            "app_id": 1,
            "app_name": "SampleApp",
            "api_type": ["REST"],
            "api_type_status": FindingStatus.CONFIRMED_YES.value,
            "auth_methods": ["API Key"],
            "credential_accessibility": CredentialAccessibility.FREE_SELF_SERVE.value,
            "overall_confidence": ConfidenceLevel.MEDIUM.value,
        }
        text = "REST API with users, accounts, create, read, update, delete operations."
        enriched = classify_app(finding, text)
        assert "api_breadth" in enriched
        assert "buildability_verdict" in enriched
        assert "toolkit_buildability_score" in enriched
        assert "mcp_status" in enriched

    def test_get_category_summary_prompt3_metrics(self):
        findings = [
            {
                "overall_confidence": "high",
                "buildability_verdict": BuildabilityVerdict.READY_TO_BUILD.value,
                "toolkit_buildability_score": 9,
                "mcp_status": MCPStatus.OFFICIAL.value,
                "auth_methods": ["OAuth2"],
            },
            {
                "overall_confidence": "medium",
                "buildability_verdict": BuildabilityVerdict.FEASIBLE.value,
                "toolkit_buildability_score": 7,
                "mcp_status": MCPStatus.COMMUNITY.value,
                "auth_methods": ["OAuth2", "API Key"],
            },
        ]
        summary = get_category_summary(findings)
        assert summary["total_apps"] == 2
        assert summary["mcp_official_count"] == 1
        assert summary["mcp_community_count"] == 1
        assert summary["has_mcp_count"] == 2
        assert summary["avg_buildability_score"] == 8.0
        assert summary["auth_method_distribution"]["OAuth2"] == 2
        assert summary["auth_method_distribution"]["API Key"] == 1


# ---------------------------------------------------------------------------
# Prompt 4: Content Validity, Quality Gates & Pilot Tests
# ---------------------------------------------------------------------------


class TestPrompt4ContentValidity:
    """Tests for detecting JS shells, login walls, and bot challenges."""

    def test_empty_content_rejected(self):
        is_valid, err = check_content_validity("<html></html>", "short")
        assert not is_valid
        assert "too short" in err.lower()

    def test_js_only_shell_detected(self):
        body = "<div>You need to enable JavaScript to run this app.</div>"
        text = "You need to enable JavaScript to run this app."
        is_valid, err = check_content_validity(body, text)
        assert not is_valid
        assert "javascript" in err.lower()

    def test_bot_challenge_detected(self):
        body = "<html><title>Just a moment...</title><body>Checking your browser before accessing. Attention Required! | Cloudflare. Ray ID: 123456</body></html>"
        text = "Checking your browser before accessing. Attention Required! | Cloudflare. Ray ID: 123456"
        is_valid, err = check_content_validity(body, text)
        assert not is_valid
        assert "challenge" in err.lower() or "denied" in err.lower()

    def test_login_wall_detected(self):
        body = "<div>Sign in to continue to Developer Portal. Please enter your email and password to access the documentation.</div>"
        text = "Sign in to continue to Developer Portal. Please enter your email and password to access the documentation."
        is_valid, err = check_content_validity(body, text)
        assert not is_valid
        assert "login" in err.lower()

    def test_valid_documentation_accepted(self):
        body = "<html><body><h1>API Reference</h1><p>The REST API allows you to manage users and webhooks using an API key.</p></body></html>"
        text = "API Reference. The REST API allows you to manage users and webhooks using an API key. Comprehensive guide."
        is_valid, err = check_content_validity(body, text)
        assert is_valid
        assert err is None


class TestPrompt4QualityGates:
    """Tests for research quality gate statuses."""

    def test_gate_passed(self):
        finding = {
            "app_id": 1,
            "app_name": "Salesforce",
            "category_name": "CRM and Sales",
            "auth_methods": ["OAuth2"],
            "credential_accessibility": CredentialAccessibility.FREE_SELF_SERVE.value,
            "api_type_status": FindingStatus.CONFIRMED_YES.value,
            "buildability_verdict": BuildabilityVerdict.READY_TO_BUILD.value,
            "overall_confidence": ConfidenceLevel.HIGH.value,
            "evidence_links": [
                {"url": "https://developer.salesforce.com/docs/apis", "source_type": "official_documentation"}
            ],
            "claim_evidence": [
                {"claim_field": "auth_methods", "claim_value": "OAuth2"}
            ],
        }
        res = evaluate_quality_gates(finding)
        assert res["status"] == QualityGateStatus.PASSED.value
        assert "valid_identity" in res["passed_checks"]
        assert "has_evidence_links" in res["passed_checks"]

    def test_gate_partial_missing_auth_evidence(self):
        finding = {
            "app_id": 2,
            "app_name": "HubSpot",
            "category_name": "CRM and Sales",
            "auth_methods": [],
            "credential_accessibility": CredentialAccessibility.UNKNOWN.value,
            "api_type_status": FindingStatus.UNKNOWN.value,
            "buildability_verdict": BuildabilityVerdict.NEEDS_INVESTIGATION.value,
            "overall_confidence": ConfidenceLevel.LOW.value,
            "evidence_links": [
                {"url": "https://developers.hubspot.com/", "source_type": "developer_portal"}
            ],
            "claim_evidence": [],
        }
        res = evaluate_quality_gates(finding)
        assert res["status"] in (QualityGateStatus.PARTIAL.value, QualityGateStatus.NEEDS_REVIEW.value)

    def test_gate_needs_review_mcp_unverified(self):
        finding = {
            "app_id": 56,
            "app_name": "Firecrawl",
            "category_name": "Data, SEO and Scraping",
            "mcp_status": MCPStatus.OFFICIAL.value,
            "mcp_repo_url": "",  # missing repo URL
            "evidence_links": [
                {"url": "https://docs.firecrawl.dev", "source_type": "official_documentation"}
            ],
        }
        res = evaluate_quality_gates(finding)
        assert res["status"] == QualityGateStatus.NEEDS_REVIEW.value
        assert "mcp_claims_verified" in res["failed_checks"]

    def test_gate_blocked_no_api(self):
        finding = {
            "app_id": 99,
            "app_name": "NoApiApp",
            "category_name": "Other",
            "api_type_status": FindingStatus.CONFIRMED_NO.value,
            "evidence_links": [
                {"url": "https://example.com/no-api", "source_type": "official_documentation"}
            ],
        }
        res = evaluate_quality_gates(finding)
        assert res["status"] == QualityGateStatus.BLOCKED.value

    def test_gate_invalid_identity(self):
        finding = {
            "app_id": 0,
            "app_name": "",
            "category_name": "",
        }
        res = evaluate_quality_gates(finding)
        assert "valid_identity" in res["failed_checks"]


class TestPrompt4PilotAndMetrics:
    """Tests for pilot application coverage and operational metrics."""

    def test_pilot_app_ids_count_and_categories(self):
        apps_data = load_apps()
        pilot_apps = [a for a in apps_data["applications"] if a["id"] in PILOT_APP_IDS]
        assert len(pilot_apps) == 10
        categories_represented = {a["category_id"] for a in pilot_apps}
        assert len(categories_represented) == 10  # exactly 1 from each category

    def test_calculate_pilot_metrics(self):
        mock_pilot_results = [
            {
                "app_id": 1,
                "app_name": "App1",
                "quality_gate_status": "passed",
                "evidence_links": [{"source_type": "official_documentation"}],
                "auth_methods": ["OAuth2"],
                "credential_accessibility": "free_self_serve",
                "mcp_status": "official_mcp",
                "research_duration_seconds": 2.0,
            },
            {
                "app_id": 2,
                "app_name": "App2",
                "quality_gate_status": "partial",
                "evidence_links": [{"source_type": "developer_portal"}],
                "auth_methods": [],
                "credential_accessibility": "unknown",
                "mcp_status": "unknown",
                "research_duration_seconds": 4.0,
            },
        ]
        metrics = calculate_pilot_metrics(mock_pilot_results, concurrency=5)
        assert metrics["applications_attempted"] == 2
        assert metrics["successfully_passed_quality_gates"] == 1
        assert metrics["partially_processed"] == 1
        assert metrics["missing_authentication_evidence"] == 1
        assert metrics["missing_credential_access_evidence"] == 1
        assert metrics["average_duration_seconds_per_app"] == 3.0
        assert metrics["estimated_full_100_apps_minutes"] > 0




if __name__ == "__main__":
    pytest.main([__file__, "-v"])

