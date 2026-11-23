"""
Frontend data contract and static asset test suite.
Validates that the dashboard dataset, demo run traces, download bundles,
and distribution artifacts adhere to the frontend data contracts.
"""

import json
from pathlib import Path
import pytest

WEB_DIR = Path(__file__).parent.parent / "web"
PUBLIC_DATA = WEB_DIR / "public" / "data"
DIST_DIR = WEB_DIR / "dist"
DOWNLOADS_DIR = WEB_DIR / "public" / "downloads"


def test_required_dashboard_json_files_exist():
    required_files = [
        "apps.json",
        "summary.json",
        "categories.json",
        "insights.json",
        "verification.json",
        "opportunities.json",
        "demo_run.json",
    ]
    for filename in required_files:
        path = PUBLIC_DATA / filename
        assert path.exists(), f"Missing required dashboard file: {filename}"
        assert path.stat().st_size > 0, f"Dashboard file is empty: {filename}"


def test_apps_json_contract_and_integrity():
    apps_path = PUBLIC_DATA / "apps.json"
    with open(apps_path, "r", encoding="utf-8") as f:
        apps = json.load(f)

    assert isinstance(apps, list)
    assert len(apps) == 100, f"Expected 100 apps, got {len(apps)}"

    # Ensure strictly sequential IDs 1 to 100
    ids = [a["app_id"] for a in apps]
    assert ids == list(range(1, 101)), "App IDs are not strictly sequential from 1 to 100"

    valid_verdicts = {"ready_to_build", "feasible", "needs_investigation", "significant_barriers"}
    valid_gates = {"passed", "partial", "needs_review", "blocked"}

    for a in apps:
        assert "app_id" in a and isinstance(a["app_id"], int)
        assert "app_name" in a and len(a["app_name"]) > 0
        assert "category_name" in a and len(a["category_name"]) > 0
        assert "priority_score" in a and 0 <= a["priority_score"] <= 100
        assert a["buildability_verdict"] in valid_verdicts
        assert a["quality_gate_status"] in valid_gates
        assert isinstance(a.get("evidence_links", []), list)


def test_summary_kpi_reconciliation():
    summary_path = PUBLIC_DATA / "summary.json"
    apps_path = PUBLIC_DATA / "apps.json"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    with open(apps_path, "r", encoding="utf-8") as f:
        apps = json.load(f)

    kpis = summary.get("kpis", {})
    assert kpis.get("total_assigned_apps") == 100
    assert kpis.get("total_researched_apps") == 100

    # Reconcile ready_to_build
    ready_count = sum(1 for a in apps if a["buildability_verdict"] == "ready_to_build")
    assert kpis.get("ready_to_build_count") == ready_count

    # Reconcile quality gate passed
    passed_count = sum(1 for a in apps if a["quality_gate_status"] == "passed")
    assert kpis.get("quality_gate_passed") == passed_count

    # Reconcile evidence backed apps
    evidence_backed = sum(1 for a in apps if len(a.get("evidence_links", [])) > 0)
    assert kpis.get("evidence_backed_apps") == evidence_backed

    # Honesty guarantee check
    assert kpis.get("measured_accuracy") is None, "Measured accuracy must be null until human audit is complete"
    assert "PENDING" in kpis.get("human_audit_status", "")


def test_demo_run_structure_and_veracity():
    demo_path = PUBLIC_DATA / "demo_run.json"
    with open(demo_path, "r", encoding="utf-8") as f:
        demo = json.load(f)

    assert demo.get("app_id") == 61
    assert demo.get("app_name") == "GitHub"
    assert "command" in demo
    assert demo.get("duration_seconds", 0) > 0
    assert demo.get("quality_gate_verdict") == "passed"
    assert len(demo.get("terminal_output", [])) >= 10

    checks = demo.get("quality_gate_checks", {})
    assert len(checks.get("passed_checks", [])) == 7
    assert len(checks.get("failed_checks", [])) == 0


def test_downloads_bundle_integrity():
    required_downloads = [
        "research_results.json",
        "research_results.csv",
        "category_summary.json",
        "verification_results.json",
        "audit_sample.json",
        "correction_log.json",
    ]
    for dl in required_downloads:
        p = DOWNLOADS_DIR / dl
        assert p.exists(), f"Missing download asset: {dl}"
        assert p.stat().st_size > 0, f"Download asset is empty: {dl}"


def test_production_build_dist_integrity():
    assert DIST_DIR.exists(), "web/dist directory does not exist. Run vite build."
    index_html = DIST_DIR / "index.html"
    assert index_html.exists(), "web/dist/index.html is missing"

    content = index_html.read_text(encoding="utf-8")
    assert "<title>" in content
    assert 'id="root"' in content

    # Check dist/data and dist/downloads exist
    dist_data = DIST_DIR / "data"
    dist_downloads = DIST_DIR / "downloads"
    assert dist_data.exists(), "web/dist/data is missing"
    assert dist_downloads.exists(), "web/dist/downloads is missing"
    assert (dist_data / "apps.json").exists(), "web/dist/data/apps.json is missing"
    assert (dist_downloads / "research_results.csv").exists(), "web/dist/downloads/research_results.csv is missing"
