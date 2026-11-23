"""
Unit tests for the accuracy scoring engine (Prompt 8).

Uses synthetic test fixtures (clearly isolated from real production data)
to test:
1. Stratified sampling reproducibility (seed 20261123)
2. Empty human audit behavior (prevents fabricated accuracy)
3. Multi-label authentication comparison (normalized set equality)
4. Exact-match dimension scoring
5. Unknown reference handling
6. Unverifiable reference exclusion & reporting
7. Equal scoring denominators between first-pass and corrected
8. Accuracy improvement calculation (percentage points)
9. Regression detection & counting
10. Prevention of fabricated accuracy metrics
"""

from __future__ import annotations

import pytest
from scripts.prepare_audit import select_audit_sample
from scripts.calculate_accuracy import (
    normalize_value,
    compare_dimension,
    score_audit_dataset,
)


# ==============================================================================
# SYNTHETIC TEST FIXTURES (DO NOT USE IN REAL REPORTS)
# ==============================================================================

@pytest.fixture
def synthetic_apps():
    """Synthetic dataset of 20 apps across 2 categories."""
    apps = []
    for i in range(1, 21):
        cat = "Category A" if i <= 10 else "Category B"
        apps.append({
            "app_id": i,
            "app_name": f"SyntheticApp_{i}",
            "category_name": cat,
            "auth_methods": ["OAuth2"] if i % 2 == 0 else ["API Key"],
            "api_type": ["REST"],
            "mcp_status": "unknown",
            "buildability_verdict": "feasible",
        })
    return apps


@pytest.fixture
def synthetic_first_pass():
    """Synthetic first-pass classifications with intentional baseline errors."""
    return {
        1: {
            "auth_methods": [],  # missed auth
            "credential_accessibility": "unknown",
            "api_type": ["REST"],
            "mcp_status": "unknown",
            "buildability_verdict": "needs_investigation",
        },
        2: {
            "auth_methods": ["OAuth2"],
            "credential_accessibility": "unknown",
            "api_type": ["REST"],
            "mcp_status": "official_mcp",  # incorrect mcp
            "buildability_verdict": "ready_to_build",
        },
    }


@pytest.fixture
def synthetic_corrected():
    """Synthetic corrected classifications after automated verification."""
    return {
        1: {
            "auth_methods": ["OAuth2"],  # corrected
            "credential_accessibility": "free_self_serve",
            "api_type": ["REST"],
            "mcp_status": "unknown",
            "buildability_verdict": "feasible",
        },
        2: {
            "auth_methods": ["OAuth2"],
            "credential_accessibility": "unknown",
            "api_type": ["REST"],
            "mcp_status": "unknown",  # corrected from official_mcp
            "buildability_verdict": "ready_to_build",
        },
    }


# ==============================================================================
# TESTS
# ==============================================================================

def test_stratified_sampling_seed_reproducibility(synthetic_apps):
    """Verify that seed 20261123 produces strictly identical sample selections."""
    sample1 = select_audit_sample(synthetic_apps, seed=20261123)
    sample2 = select_audit_sample(synthetic_apps, seed=20261123)

    assert [a["app_id"] for a in sample1] == [a["app_id"] for a in sample2]
    assert len(sample1) == 4  # 2 categories x 2 apps


def test_empty_human_audit_prevents_fabricated_accuracy(synthetic_first_pass, synthetic_corrected):
    """Verify that empty human judgments yield NOT MEASURED, never a fabricated percentage."""
    empty_reviews = [
        {
            "app_id": 1,
            "app_name": "App1",
            "review_completion_status": "PENDING_HUMAN_REVIEW",
            "human_verified_auth_methods": "",
            "human_verified_credential_access": "",
            "human_verified_api_surface": "",
            "human_verified_mcp_status": "",
            "human_verified_buildability_verdict": "",
        }
    ]

    metrics = score_audit_dataset(empty_reviews, synthetic_first_pass, synthetic_corrected)
    assert metrics["status"] == "HUMAN_AUDIT_PENDING"
    assert "NOT YET MEASURED" in metrics["status_message"]
    assert metrics["first_pass_accuracy"] is None
    assert metrics["corrected_accuracy"] is None
    assert metrics["accuracy_improvement_points"] is None


def test_multi_label_authentication_comparison():
    """Verify normalized set comparison for multi-label auth methods."""
    # Order independence
    assert compare_dimension("auth_methods", ["OAuth2", "API Key"], ["API Key", "OAuth2"]) is True
    # String with delimiter
    assert compare_dimension("auth_methods", "OAuth2, API Key", ["API Key", "OAuth2"]) is True
    assert compare_dimension("auth_methods", "OAuth2 | API Key", ["API Key", "OAuth2"]) is True
    # Mismatch
    assert compare_dimension("auth_methods", ["OAuth2"], ["OAuth2", "API Key"]) is False


def test_exact_match_dimensions():
    """Verify exact-match logic on buildability verdict and MCP status."""
    assert compare_dimension("buildability_verdict", "ready_to_build", "ready_to_build") is True
    assert compare_dimension("buildability_verdict", "Ready_To_Build", "ready_to_build") is True
    assert compare_dimension("buildability_verdict", "feasible", "ready_to_build") is False

    assert compare_dimension("mcp_status", "official_mcp", "official_mcp") is True
    assert compare_dimension("mcp_status", "community_mcp", "official_mcp") is False


def test_unverifiable_reference_exclusion(synthetic_first_pass, synthetic_corrected):
    """Verify that UNVERIFIABLE human labels are excluded from denominator."""
    synthetic_reviews = [
        {
            "app_id": 1,
            "human_verified": True,
            "human_verified_auth_methods": "OAuth2",
            "human_verified_credential_access": "UNVERIFIABLE",  # should be excluded
            "human_verified_api_surface": "REST",
            "human_verified_mcp_status": "unknown",
            "human_verified_buildability_verdict": "feasible",
        }
    ]

    metrics = score_audit_dataset(synthetic_reviews, synthetic_first_pass, synthetic_corrected)
    assert metrics["excluded_unverifiable_pairs"] == 1
    assert metrics["scorable_app_field_pairs"] == 4  # 5 minus 1


def test_accuracy_improvement_and_equal_denominators(synthetic_first_pass, synthetic_corrected):
    """Verify identical denominators and exact improvement calculation."""
    synthetic_reviews = [
        {
            "app_id": 1,
            "human_verified": True,
            "human_verified_auth_methods": "OAuth2",      # FP: [] (wrong), Cur: OAuth2 (right) -> Improved!
            "human_verified_credential_access": "free_self_serve",
            "human_verified_api_surface": "REST",         # Both right
            "human_verified_mcp_status": "unknown",       # Both right
            "human_verified_buildability_verdict": "feasible",  # FP: needs_investigation, Cur: feasible -> Improved!
        }
    ]

    metrics = score_audit_dataset(synthetic_reviews, synthetic_first_pass, synthetic_corrected)
    assert metrics["status"] == "MEASURED"
    assert metrics["scorable_app_field_pairs"] == 5

    # First-pass correct: api_type (REST), mcp (unknown) -> 2/5 = 40%
    assert metrics["first_pass_correct"] == 2
    assert metrics["first_pass_accuracy"] == 40.0

    # Corrected correct: auth (OAuth2), creds (free), api (REST), mcp (unknown), build (feasible) -> 5/5 = 100%
    assert metrics["corrected_correct"] == 5
    assert metrics["corrected_accuracy"] == 100.0

    # Improvement = 100 - 40 = 60.0 percentage points
    assert metrics["accuracy_improvement_points"] == 60.0
    assert metrics["improved_count"] == 3


def test_regression_detection(synthetic_first_pass, synthetic_corrected):
    """Verify that regressions (first-pass correct, corrected wrong) are detected."""
    reviews = [
        {
            "app_id": 2,
            "human_verified": True,
            # Let's say human says MCP was indeed official_mcp
            "human_verified_mcp_status": "official_mcp",
        }
    ]
    # In synthetic: FP had "official_mcp" (correct), Cur had "unknown" (wrong -> regression!)
    metrics = score_audit_dataset(reviews, synthetic_first_pass, synthetic_corrected)
    assert metrics["regressed_count"] == 1
    assert metrics["first_pass_accuracy"] == 100.0
    assert metrics["corrected_accuracy"] == 0.0
    assert metrics["accuracy_improvement_points"] == -100.0
