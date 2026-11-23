# Automated Evidence Verification & Error Detection Methodology

## 1. Overview & Purpose

This document outlines the multi-layer automated verification architecture built for the **Composio AI Product Ops** research agent. In production integrations, superficial completeness is dangerous; an inaccurate API classification can lead to failed customer onboarding, broken agent workflows, or wasted development sprints.

The verification system provides an independent, reproducible auditing pipeline that examines every collected claim, identifies contradictions, enforces evidence grounding, and logs a transparent correction trail.

---

## 2. Four-Layer Verification System

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: STRUCTURAL VALIDATION                              │
│ Schema compliance, enum values, ID uniqueness (1-100)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ LAYER 2: EVIDENCE GROUNDING & HTTP VERIFICATION             │
│ Check source HTTP status (200), excerpt text match, context │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ LAYER 3: CROSS-CHECKING & CONTRADICTION DETECTION           │
│ Multi-domain corroboration, conflicting auth/pricing rules │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ LAYER 4: SAFE AUTO-CORRECTION & HUMAN AUDIT PREPARATION     │
│ Correction log, quality gate demotion, stratified queue     │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1 — Structural Validation
- **Scope**: Evaluates every finding for schema completeness, valid data types, required fields, and enum conformity.
- **Enforcement**: Strictly checks `app_id` (1–100), categories (10 unique, 10 per category), and enum constraints for `AuthMethod`, `APIType`, `APIBreadth`, `MCPStatus`, `BuildabilityVerdict`, and `QualityGateStatus`.
- **Note**: Structural validity verifies data hygiene; it does not constitute factual accuracy.

### Layer 2 — Evidence Grounding & HTTP Verification
- **Reachability Check**: Confirms that cited URLs returned HTTP 200 with non-empty content bodies. URLs blocked by WAFs (HTTP 403), dead links (HTTP 404), or server errors (HTTP 500) are flagged as `source_unavailable`.
- **Excerpt Grounding**: Verifies that the cited text excerpt genuinely appears in the retrieved source body.
- **Domain Relevance**:
  - `auth_methods`: Excerpt must contain authentication-specific keywords (`oauth`, `bearer`, `api key`, `token`, `credentials`).
  - `api_type`: Excerpt must explicitly define API interaction models (`rest`, `graphql`, `grpc`, `endpoint`, `webhook`).
  - `mcp_status`: Excerpt must reference Model Context Protocol terms (`mcp`, `modelcontextprotocol`).

### Layer 3 — Independent Cross-Checking & Contradiction Detection
The engine evaluates multi-source findings against known integration contradictions:
1. **OAuth-Only Contradiction**: Claim is OAuth-only, but documentation explicitly references API keys or personal access tokens.
2. **Buildable-Now with Blockers**: Claim is `ready_to_build`, but documentation indicates `no_public_api` or mandatory enterprise sales access.
3. **Official MCP Without Vendor Repo**: Claim is `official_mcp`, but source URL is an unverified user repository rather than an official vendor organization.
4. **Excerpt Mismatch**: The claim cites a specific excerpt, but the excerpt does not contain or mention the claimed entity (e.g. claims GraphQL from an excerpt that only discusses REST).
5. **Multi-Domain Corroboration**: When claims are confirmed by two or more distinct domains (e.g., `docs.github.com` and `github.com`), status is upgraded to `corroborated_by_independent_source`.

### Layer 4 — Human Review Flagging & Audit Queue Preparation
- Any finding with detected contradictions, low confidence ratings, or nonstandard application surfaces is flagged for human review.
- Generates a structured queue in `data/human_audit_queue.json` containing:
  - **Stratified Random Sample**: 10 applications (1 randomly chosen per category with reproducible seed `42`).
  - **Risk-Based Priority Sample**: 34 high-risk applications (e.g., Salesforce WAF 403, Sherlock CLI, NotebookLM, PitchBook, DealCloud).
  - Specific reviewer questions and unpopulated human judgment fields.

---

## 3. Claim Verification Status Taxonomy

Every verified claim receives one of 7 standardized statuses:

| Status | Meaning |
|---|---|
| `verified_by_primary_source` | Claim is directly grounded in retrieved primary documentation excerpts with HTTP 200 verification. |
| `corroborated_by_independent_source` | Claim is independently confirmed across two or more distinct web domains. |
| `needs_human_review` | Unverified claim, unconfirmed MCP server, or ambiguous integration model requiring manual inspection. |
| `unsupported` | Claimed value is not found in the cited source text. |
| `contradicted` | Claim directly conflicts with retrieved documentation (e.g. claiming no API keys when text mentions API keys). |
| `source_unavailable` | Documentation URL failed to load (HTTP 403 WAF challenge, HTTP 404, or timeout). |
| `not_checked` | Reserved for fields where no active claim was asserted (e.g., unknown status preserved). |

---

## 4. Safe Automatic Correction Rules

Automatic corrections are only applied under strict criteria to prevent introducing automated hallucinations:
1. **Rule 1 (MCP Demotion)**: If an application claims `official_mcp` but lacks official vendor organization repository proof, it is safely demoted to `mcp_unverified`.
2. **Rule 2 (Buildability Alignment)**: If an application is claimed as `ready_to_build` (score 8–10) but lacks verified API endpoints or was blocked by WAF (e.g., Salesforce), it is safely downgraded to `needs_investigation` (score 4).
3. **Rule 3 (Quality Gate Demotion)**: If an application's quality gate was marked `passed` but one or more claims are unsupported or contradicted, the gate is demoted to `partial` or `needs_review`.
4. **Correction Provenance**: All modifications are logged in `data/correction_log.json` detailing original value, corrected value, rationale, timestamp, and human approval requirement.

---

## 5. Accuracy Measurement Limitations & Honesty Principles

- **Coverage vs. Accuracy**: Verification coverage (e.g., 54.0% of claims verified by primary sources) indicates evidence grounding rate, **not ground-truth accuracy**.
- **No Self-Declared 100% Accuracy**: The system does not claim 100% accuracy based on automated script execution alone. True factual accuracy requires human auditing against ground-truth reference data.
- **Traceability Guarantee**: First-pass baseline snapshots (`data/batch1_first_pass.json` and `data/batch2_first_pass.json`) remain strictly immutable.

---

## 6. Human Audit Protocol & Accuracy Scoring (Prompt 8)

### Stratified Sampling Methodology
To scientifically validate research findings against independent ground truth, the audit framework isolates a representative sample of 20 applications:
- **Seed**: `20261123` (deterministic pseudo-random generator).
- **Stratification**: Exactly 2 applications from each of the 10 categories.
- **Diversity**: Mix of high-confidence (`passed`), partial (`partial`), needs review (`needs_review`), and nonstandard tools (e.g. `Mermaid CLI`).
- **Storage**: Exported to `data/audit_sample.json`.

### Human Review Protocol & Worksheet
- **Blank Template**: Exported to `data/human_audit_template.csv` with all human judgment fields left blank by design.
- **Audit Interface**: A self-contained HTML worksheet at `data/audit_interface.html` displaying first-pass vs corrected findings, retrieved documentation links, cited excerpts, and editable review forms with JSON/CSV export capabilities.
- **Strict Policy**: The automated pipeline never populates human judgments automatically. If human judgments are unpopulated, accuracy metrics remain strictly reported as `NOT MEASURED`.

### Five Core Scoring Dimensions
Human evaluators score five technical dimensions:
1. **Authentication Methods**: Normalized set comparison (e.g. `{'OAuth2', 'API Key'}` equals `{'API Key', 'OAuth2'}`).
2. **Credential Accessibility**: Tier match against verified pricing/access documentation (`free_self_serve`, `contact_sales`, etc.).
3. **API Surface**: Normalized endpoint protocol sets (`REST`, `GraphQL`, `CLI Only`, etc.).
4. **Existing MCP Status**: Exact match against official or community repositories.
5. **Buildability Verdict**: Exact match against integration viability tiers.

### Equal Denominators & Unverifiable Handling
- **Equal Denominators**: Both first-pass and corrected accuracy are scored over the exact same set of scorable audited pairs.
- **Unverifiable Labels**: Only excluded when a human reviewer explicitly flags a feature as `UNVERIFIABLE` due to missing public documentation (e.g., enterprise-gated APIs). Exclusions are tracked and reported in `excluded_unverifiable_pairs`.

---

## 7. How to Reproduce Verification & Accuracy Scoring

```bash
# 1. Run the verification engine (4 layers)
python -m agent.verify

# 2. Run dataset schema validation (12 checks)
python scripts/validate_research.py

# 3. Generate the 20-app audit sample and human template
python scripts/prepare_audit.py

# 4. Generate the standalone HTML audit interface
python scripts/build_audit_ui.py

# 5. Run independent cross-checks on the sample
python scripts/cross_check_sample.py

# 6. Run accuracy calculation engine
python scripts/calculate_accuracy.py

# 7. Run automated verification unit tests (104 tests)
python -m pytest tests/ -v

# 8. Validate dashboard data export integrity (10 checks)
python scripts/validate_dashboard_data.py
```

---

## 8. Prompt 10 Verification Closure & Dashboard Integrity

In Prompt 10, the verification state was closed and reconciled for the frontend web application:
- **Reconciled Correction Log**: 3 safe automatic demotions applied to date (Apify, BigCommerce, Firecrawl demoted from `passed` to `partial` due to unextracted auth terms).
- **Audit Sample Preservation**: 20-app stratified sample and blank human worksheet preserved without modification.
- **Strict Ground-Truth Honesty**: Status confirmed as `HUMAN AUDIT PENDING — ACCURACY NOT YET MEASURED`. Accuracy scores remain strictly `null` in `web/public/data/summary.json` and `web/public/data/verification.json`.
- **Export Validation**: All frontend files in `web/public/data/` validated via `scripts/validate_dashboard_data.py` (10/10 checks passing).
