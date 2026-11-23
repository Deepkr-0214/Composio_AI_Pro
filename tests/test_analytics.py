"""
Automated unit tests for Research Analytics & Pattern Discovery Engine (Prompt 9).

Tests:
- Priority score computation logic and weights (0-100 range, component boundaries).
- Opportunity grouping logic (A through E mutual exclusivity and completeness).
- Top 10 integration opportunities selection and ordering.
- Outreach candidate generation.
- Executive insights generation and structure.
- Generated analytics artifacts validation (category comparisons, analytics summary, priorities).
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.analyze_research import (
    compute_priority_score,
    categorize_opportunity_groups,
    generate_top_opportunities,
    generate_outreach_candidates,
    generate_executive_insights,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"


class TestPriorityScoring:
    """Test priority scoring heuristic logic and breakdown."""

    def test_ideal_application_score(self):
        """An application with optimal access, extensive API, and official MCP should score near 100."""
        app = {
            "app_id": 999,
            "credential_accessibility": "free_self_serve",  # 30 pts
            "api_breadth": "extensive",                     # 15 pts
            "api_type": ["REST", "GraphQL"],                # 10 pts
            "auth_methods": ["API Key"],                    # 15 pts
            "mcp_status": "official_mcp",                   # 10 pts
            "quality_gate_status": "passed",                # doc quality
            "evidence_quality_score": 0.95,                 # 10 pts
            "blockers": [],                                 # 10 pts
            "evidence_links": [{"url": "https://example.com/api"}],
        }
        res = compute_priority_score(app)
        assert res["priority_score"] == 100
        assert res["score_status"] == "SCORED"
        assert res["breakdown"]["credential_accessibility_pts"] == 30
        assert res["breakdown"]["api_capability_pts"] == 25
        assert res["breakdown"]["auth_complexity_pts"] == 15
        assert res["breakdown"]["mcp_availability_pts"] == 10
        assert res["breakdown"]["doc_quality_pts"] == 10
        assert res["breakdown"]["blocker_pts"] == 10

    def test_restricted_application_score(self):
        """A strictly gated enterprise application with no public API should score very low."""
        app = {
            "app_id": 998,
            "credential_accessibility": "enterprise_only",  # 2 pts
            "api_breadth": "unknown",                       # 0 pts
            "api_type": ["unknown"],                        # 0 pts
            "auth_methods": ["unknown"],                    # 2 pts
            "mcp_status": "no_mcp",                         # 0 pts
            "quality_gate_status": "needs_review",          # 1 pt
            "evidence_quality_score": 0.1,
            "blockers": ["no_public_api"],                  # 1 pt
            "evidence_links": [],
        }
        res = compute_priority_score(app)
        assert res["priority_score"] == 6
        assert res["score_status"] == "PROVISIONAL_LOW_EVIDENCE"
        assert res["breakdown"]["credential_accessibility_pts"] == 2
        assert res["breakdown"]["blocker_pts"] == 1

    def test_score_boundaries_on_actual_dataset(self):
        """All 100 applications in research_results.json must score between 0 and 100."""
        results_file = DATA_DIR / "research_results.json"
        with open(results_file, "r", encoding="utf-8") as f:
            apps = json.load(f)

        assert len(apps) == 100
        for app in apps:
            res = compute_priority_score(app)
            assert 0 <= res["priority_score"] <= 100
            assert res["score_status"] in ("SCORED", "PROVISIONAL_LOW_EVIDENCE")


class TestOpportunityGrouping:
    """Test classification of applications into analytical groups A through E."""

    @pytest.fixture
    def dataset_and_priorities(self):
        results_file = DATA_DIR / "research_results.json"
        with open(results_file, "r", encoding="utf-8") as f:
            apps = json.load(f)
        priorities = [
            {"app_id": a["app_id"], **compute_priority_score(a)}
            for a in apps
        ]
        return apps, priorities

    def test_opportunity_groups_completeness_and_exclusivity(self, dataset_and_priorities):
        apps, priorities = dataset_and_priorities
        groups = categorize_opportunity_groups(apps, priorities)

        all_group_keys = [
            "group_a_quick_wins",
            "group_b_conditional",
            "group_c_outreach_required",
            "group_d_further_investigation",
            "group_e_no_confirmed_path",
        ]

        assigned_app_ids = []
        for key in all_group_keys:
            assert key in groups
            for item in groups[key]:
                assigned_app_ids.append(item["app_id"])

        # Exactly 100 apps assigned
        assert len(assigned_app_ids) == 100
        # No duplicates
        assert len(set(assigned_app_ids)) == 100

    def test_specific_group_assignments(self, dataset_and_priorities):
        apps, priorities = dataset_and_priorities
        groups = categorize_opportunity_groups(apps, priorities)

        # Sherlock CLI (58) and Mermaid CLI (98) must be in Group E
        group_e_ids = {item["app_id"] for item in groups["group_e_no_confirmed_path"]}
        assert 58 in group_e_ids
        assert 98 in group_e_ids

        # DealCloud (10), Meta Ads (32), PitchBook (90) must be in Group C
        group_c_ids = {item["app_id"] for item in groups["group_c_outreach_required"]}
        assert 10 in group_c_ids
        assert 32 in group_c_ids
        assert 90 in group_c_ids

        # GitHub (61) should be in Group A (Quick Wins)
        group_a_ids = {item["app_id"] for item in groups["group_a_quick_wins"]}
        assert 61 in group_a_ids


class TestTopOpportunitiesAndOutreach:
    """Test top 10 opportunity selection and outreach candidate generation."""

    @pytest.fixture
    def apps(self):
        results_file = DATA_DIR / "research_results.json"
        with open(results_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_top_opportunities_selection(self, apps):
        priorities = [
            {"app_id": a["app_id"], **compute_priority_score(a)}
            for a in apps
        ]
        top10 = generate_top_opportunities(apps, priorities)

        assert len(top10) == 10
        # Ranked descending by priority_score
        scores = [item["priority_score"] for item in top10]
        assert scores == sorted(scores, reverse=True)

        for item in top10:
            assert item["verification_status"] in ("passed", "partial")
            assert len(item["supporting_documentation_urls"]) > 0
            assert item["main_reason"]
            assert item["remaining_risk"]

    def test_outreach_candidates(self, apps):
        candidates = generate_outreach_candidates(apps)
        assert len(candidates) >= 5

        cand_names = {c["app_name"] for c in candidates}
        assert "Salesforce" in cand_names
        assert "DealCloud" in cand_names
        assert "Meta Ads" in cand_names
        assert "PitchBook" in cand_names

        for cand in candidates:
            assert cand["confirmed_access_restriction"]
            assert cand["required_approval_or_commercial_step"]
            assert cand["technical_feasibility"]
            assert cand["suggested_action"]


class TestExecutiveInsightsAndArtifacts:
    """Test executive insight generation and artifact integrity."""

    def test_executive_insights_structure(self):
        summary_file = DATA_DIR / "analytics_summary.json"
        cat_file = DATA_DIR / "category_comparison.json"
        results_file = DATA_DIR / "research_results.json"

        with open(results_file, "r", encoding="utf-8") as f:
            apps = json.load(f)
        with open(summary_file, "r", encoding="utf-8") as f:
            summary = json.load(f)
        with open(cat_file, "r", encoding="utf-8") as f:
            cat_comp = json.load(f)

        insights = generate_executive_insights(
            apps,
            summary["authentication_distribution"],
            cat_comp,
            summary["mcp_distribution"],
        )

        assert len(insights) == 5
        for ins in insights:
            assert ins["insight_id"].startswith("INSIGHT-")
            assert ins["headline"]
            assert ins["explanation"]
            assert ins["metric"]
            assert ins["denominator"]
            assert len(ins["supporting_apps"]) > 0
            assert ins["evidence_reference"]
            assert ins["limitation"]

    def test_analytics_artifacts_exist_and_valid(self):
        """Verify all generated files exist and contain valid data."""
        expected_files = [
            DATA_DIR / "analytics_summary.json",
            DATA_DIR / "category_comparison.json",
            DATA_DIR / "integration_priorities.json",
            DATA_DIR / "top_opportunities.json",
            DATA_DIR / "outreach_candidates.json",
            DATA_DIR / "executive_insights.json",
            DOCS_DIR / "research_insights.md",
        ]

        for p in expected_files:
            assert p.exists(), f"Missing expected artifact: {p}"
            assert p.stat().st_size > 0, f"Artifact is empty: {p}"

        with open(DATA_DIR / "category_comparison.json", "r", encoding="utf-8") as f:
            cats = json.load(f)
            assert len(cats) == 10
            for name, data in cats.items():
                assert data["assigned_apps"] == 10
                assert "average_buildability_score" in data
                assert "completeness_rate" in data
