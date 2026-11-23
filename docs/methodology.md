# Research Methodology & Evidence Classification

## Overview

This document details the methodology used by the Composio AI Product Ops Research Agent to systematically investigate 100 applications across 10 categories. The research pipeline automatically identifies API protocols, authentication types, developer credential access, MCP server support, and agent toolkit buildability, all grounded in verifiable documentation evidence.

---

## 1. Evidence Hierarchy

To ensure strict factual accuracy and avoid hallucinations, the agent prioritizes sources in descending order of reliability:

1. **Tier 1: Official Developer Documentation & API References**
   - Direct documentation portals maintained by the vendor (e.g., `docs.github.com`, `docs.stripe.com`, `developers.hubspot.com`).
   - Highest weight for endpoint specs, auth protocols, rate limits, and scopes.

2. **Tier 2: Official Authentication & Security Guides**
   - Vendor documentation explicitly detailing OAuth2 flows, API keys, tokens, and credential management.

3. **Tier 3: Official Developer Portals & Getting Started Guides**
   - High-level overview of capabilities, onboarding friction, and credential self-service rules.

4. **Tier 4: Official GitHub Repositories**
   - Verified vendor GitHub organizations (e.g., `github.com/twentyhq/twenty`, `github.com/firecrawl/firecrawl`).
   - Essential for verifying open-source toolkits, SDKs, and community contributions.

5. **Tier 5: Model Context Protocol (MCP) Registries & Repositories**
   - MCP servers registered under official vendor organizations or trusted community implementations.

6. **Tier 6: Secondary & Third-Party Documentation**
   - Used only when primary sources are inaccessible, and always explicitly labeled as `third_party` or `unverified`.

---

## 2. Classification Taxonomy & Rubrics

### A. Authentication Methods (10 Types)

The agent supports multi-auth detection across:
- **OAuth 2.0**: Authorization code, client credentials, PKCE flows.
- **API Key**: Static token passed via query parameter or custom HTTP header (e.g. `x-api-key`).
- **Bearer Token**: Standard `Authorization: Bearer <token>` authorization.
- **Personal Access Token (PAT)**: User-scoped long-lived token generated in developer/account settings.
- **Basic Auth**: HTTP Basic username/password base64-encoded.
- **Service Account**: Server-to-server cryptographic credentials (e.g. Google Cloud, Firebase).
- **JWT**: JSON Web Token with signed claims.
- **HMAC**: Request signing with cryptographic hashes.
- **Session Based**: Cookie or session ID-based browser authentication.
- **Custom / Unknown**: Proprietary or undocumented authentication schemes.

### B. Developer Credential Accessibility (10 Tiers)

Classifies the friction required to obtain API keys/credentials:
- `free_self_serve`: Instant self-serve signup with immediate API credentials; no credit card required.
- `trial_self_serve`: Time-limited trial with instant access.
- `paid_self_serve`: Self-serve instant signup requiring a paid credit card plan.
- `admin_approval`: Requires workspace/tenant organization admin approval.
- `app_review_required`: App manifest/integration must undergo manual vendor review before access.
- `partner_approval`: Restricted to approved ecosystem partners.
- `contact_sales`: Sales outreach required to negotiate API access.
- `enterprise_only`: Exclusively available on top-tier custom enterprise contracts.
- `no_hosted_credentials`: Local/open-source software requiring self-hosting without cloud credentials.
- `unknown`: Insufficient documentation to determine credential onboarding friction.

### C. API Surface & Breadth Rubric

API breadth is classified based on keyword density and entity coverage:
- **Extensive**: Large multi-domain API surface with 12+ entity types and advanced capabilities (batching, webhooks, filtering, pagination).
- **Broad**: Covers 7–11 entity types with full CRUD and operational capabilities.
- **Moderate**: Covers 4–6 core entity types with standard workflows.
- **Narrow**: 1–3 endpoints or specialized ping/status operations only.
- **Unknown**: Insufficient evidence to determine API scope.

Every breadth classification includes an explicit textual justification.

### D. Model Context Protocol (MCP) Support

MCP availability is categorized into five explicit states:
- `official_mcp`: Vendor-maintained official MCP server (with repository URL).
- `community_mcp`: Verified third-party/community MCP implementation.
- `mcp_in_progress`: Documented in-flight MCP development or roadmap item.
- `mcp_unverified`: MCP mentioned in documentation without repository verification.
- `unknown`: No documented MCP presence.

### E. AI Agent Toolkit Buildability Scoring

Evaluates the feasibility of building a Composio tool integration on a 1–10 numeric scale:
- **Ready to Build (8–10)**: Public REST/GraphQL APIs, standard OAuth2/API keys, free or self-serve credentials, no gating blockers.
- **Feasible (6–7)**: Standard APIs available, minor friction in credentials or rate limits.
- **Needs Investigation (4–5)**: Moderate ambiguity, missing documentation segments, or unverified credential flows.
- **Significant Barriers (2–3)**: Heavy gating, partner approvals, sales contact, or complex legacy auth.
- **Not Feasible (1)**: Confirmed absent API (`no_public_api`), deprecated interfaces, or legal/licensing restrictions.

### F. Blocker Types

Specific obstacles identified by the agent:
- `no_public_api`: Vendor confirmed no public developer API exists.
- `deprecated_api`: API deprecated or scheduled for sunset.
- `undocumented_api`: Endpoints reverse-engineered or private.
- `credential_barrier`: Opaque credential provisioning.
- `partner_only_access`: API restricted to certified partners.
- `enterprise_only_access`: Only available to enterprise contract tiers.
- `rate_limit_too_strict`: Limits prevent practical agent polling or tool use.
- `no_sandbox`: No testing environment provided.
- `legal_restriction`: Terms of service forbid AI scraping or programmatic access.

---

## 3. Claim-Level Evidence Architecture

Every finding contains atomic claim evidence linking each extracted attribute back to its exact origin:
```json
{
  "claim_field": "auth_methods",
  "claim_value": "OAuth2",
  "source_url": "https://docs.firecrawl.dev/api-reference/introduction",
  "source_title": "Introduction - Firecrawl Docs",
  "supporting_excerpt": "...use OAuth for apps. Authentication compares every option...",
  "retrieved_at": "2026-11-23T11:38:20.664614+00:00",
  "confidence": "medium",
  "verification_status": "unverified"
}
```

---

## 4. Evidence Quality Validation & Research Quality Gates

The engine runs automated post-extraction quality checks:
- **Missing URLs**: Flags evidence links without resolvable URLs.
- **Unverified MCP Claims**: Flags official/community MCP classifications that lack repository URLs.
- **Buildability Inconsistencies**: Flags applications classified as `ready_to_build` when their API status is `unknown` or `confirmed_no`.
- **Auth vs Credential Gaps**: Flags applications with confirmed authentication methods whose credential accessibility remains `unknown`.
- **Quality Score**: Computes a 0.0–1.0 score reflecting the completeness and consistency of evidence.

### Formal Quality Gates (`evaluate_quality_gates`)

Every application finding is evaluated against strict research gates:
- **`passed`**: All gates satisfied, high/medium confidence, verified API or authentication evidence backed by official documentation.
- **`partial`**: Valid links present, but data is incomplete (e.g. low confidence, missing auth details, or gaps in credential documentation).
- **`needs_review`**: Unresolved discrepancies, unverified MCP assertions, or zero retrievable evidence.
- **`blocked`**: Public API confirmed absent (`confirmed_no`), integration deemed `not_feasible`, or documentation paywalled/forbidden.

---

## 5. Content Validity & Anti-Bot Traps

Modern developer portals frequently return HTTP 200 while displaying non-documentation payloads:
- **Client-Side Rendering (CSR) Traps**: Empty single-page app containers (`<div id="root"></div>`) or "Please enable JavaScript".
- **Bot Challenge Walls**: Cloudflare Turnstile, "Just a moment...", or "Checking your browser".
- **Login Walls**: "Sign in to continue to Developer Portal".

The fetcher runs `check_content_validity()` on all HTTP 200 bodies. Responses falling into these categories are classified as `BLOCKED` or `FAILED` rather than being falsely indexed as valid documentation.

---

## 5. Unknown vs. Confirmed Negative

A fundamental principle of this research is avoiding false negatives:
- An unresearched or unfound attribute is labeled `FindingStatus.UNKNOWN`.
- An attribute is only marked `FindingStatus.CONFIRMED_NO` if explicit documentation states that the feature is unsupported (e.g. "We do not provide public API keys").
- Inaccessible or blocked pages never serve as evidence that an API does not exist.

---

## 6. Defensive Crawling & Bounded Scraping

- **Robots.txt Adherence**: Crawlers respect `robots.txt` disallows for the `*` user agent. Blocked pages are logged as `blocked` without throwing unhandled exceptions.
- **Fail-Fast Timeouts**: Individual page requests are capped at 8.0s timeout. Application investigations are capped at 25.0s total.
- **Per-Domain Rate Limiting**: A mandatory 1.0s delay is enforced between sequential requests to the same domain.
- **Redirect Transparency**: The pipeline tracks both original candidate URLs and final resolved URLs after HTTP redirects (e.g. 301/308).

---

## 7. Traceability & Ground Truth Verification

- **Batch Execution & Immutability**:
  - The 100 applications were executed in two discrete batches:
    - **Batch 1 (Apps 1–50)**: Preserved immutably in `data/batch1_first_pass.json`.
    - **Batch 2 (Apps 51–100)**: Preserved immutably in `data/batch2_first_pass.json`.
  - Full merged results across all 100 applications reside in `data/research_results.json` and tabular `data/research_results.csv`.
  - Operational benchmarks and metrics are tracked in `data/research_metrics.json` and `data/category_summary.json`.

---

## 8. Nonstandard Integration Surfaces & Edge Cases

Not all modern software fits conventional HTTP REST/GraphQL patterns. The research agent explicitly accounts for nonstandard applications without forcing them into conventional paradigms:
- **CLI & Local Open-Source Tools** (e.g. `Sherlock`, `Mermaid CLI`): Primarily distributed as npm packages or Python packages with terminal commands rather than hosted SaaS APIs.
- **Consumer vs. Enterprise Surfaces** (e.g. `NotebookLM`): Consumer interface lacks a public developer API, while enterprise Google Cloud Vertex AI integrations follow separate governance.
- **Enterprise-Gated / Commercial Data Services** (e.g. `PitchBook`, `Consensus`, `Binance`, `QuickBooks`): API access requires proprietary partner vetting, financial credentialing, or sales contracts.
- **Ambiguous Vendor Identity / Missing Portals** (e.g. `Paygent Connect`, `iPayX`, `systeme.io`): Lack standardized developer subdomains (`developers.*`), requiring manual verification and disambiguation.
- **Specialized Protocol APIs** (e.g. `YouTube Transcript`): Relies on internal or specialized endpoint wrappers rather than standard YouTube Data API v3 endpoints.

---

## 9. Independent Verification & Ground-Truth Architecture (Prompt 7 & 8)

The research pipeline uses a multi-layered verification system:
- **Candidate Pool (`data/verification_candidates.json`)**: Tracks 73 targeted investigation candidates (low confidence, WAF-blocked, nonstandard CLI tools, MCP claims, high buildability claims) and a 10-application stratified category sample.
- **Verification Engine (`agent/verify.py`)**: Executes 4 layers of automated contradiction detection and claim cross-checks, preserving an immutable log of demotions (`data/correction_log.json`).
- **Human Audit Interface (`data/audit_interface.html`)**: Interactive standalone worksheet for reviewing the 20-app stratified sample (seed `20261123`).
- **Ground-Truth Honesty**: Reports `HUMAN AUDIT PENDING — ACCURACY NOT YET MEASURED` until real human evaluations are submitted.

---

## 10. Integration Priority Scoring & Analytical Opportunity Framework (Prompt 9)

To translate raw classification outputs into actionable product operations decisions, the research pipeline includes an objective scoring and categorization engine (`scripts/analyze_research.py`).

### A. Integration Priority Score (0–100 Scale)

The priority score represents the immediacy and commercial return of developing an agent toolkit for a given platform. It is calculated across six weighted dimensions:

$$\text{Priority Score} = S_{\text{cred}} + S_{\text{api}} + S_{\text{auth}} + S_{\text{mcp}} + S_{\text{doc}} + S_{\text{blocker}}$$

| Dimension | Max Pts | Weight | Scoring Rubric |
|:---|:---:|:---:|:---|
| **Credential Accessibility** | 30 | 30% | `free_self_serve`: 30, `trial_self_serve`: 25, `paid_self_serve`: 20, `admin_approval`: 15, `app_review_required`: 10, `partner_approval`: 5, `contact_sales` / `enterprise_only`: 2, `unknown`: 5 |
| **API Capability** | 25 | 25% | **Breadth (15 pts)**: `extensive`: 15, `broad`: 12, `moderate`: 8, `narrow`: 4, `unknown`: 0.<br>**Surfaces (10 pts)**: REST + GraphQL: 10, REST or GraphQL: 8, other confirmed: 4, none/unknown: 0 |
| **Authentication Complexity** | 15 | 15% | API Key or Bearer Token only: 15, API Key + OAuth2: 13, OAuth2: 12, Basic Auth: 10, Other: 8, Unknown: 2 |
| **MCP Availability** | 10 | 10% | `official_mcp`: 10, `community_mcp`: 7, `mcp_in_progress` / `mcp_unverified`: 4, `unknown`: 0 |
| **Documentation Quality** | 10 | 10% | Passed quality gate & score $\ge 0.8$: 10, Passed: 8, Partial: 5, Needs Review / Blocked: 1 |
| **Integration Blockers** | 10 | 10% | No blockers: 10, Minor limits / webhook friction: 6, Credential / complex auth: 4, Enterprise / partner gate: 1 |

Applications with confirmed evidence links are designated `"SCORED"`; applications with zero retrieved documentation are designated `"PROVISIONAL_LOW_EVIDENCE"`.

### B. Five Opportunity Groups

Every investigated application is mapped into exactly one mutually exclusive analytical group:
1. **Group A — Quick Wins**: Ready-to-build verdict, passed quality gate, verified API and auth, priority score $\ge 55$. High immediate payoff with minimal onboarding friction (e.g. GitHub, Netlify, Close, Asana).
2. **Group B — Conditional Opportunities**: Feasible verdict or buildability score $\ge 6$. Standard APIs available, but require addressing pagination, rate limits, or OAuth app approval (e.g. Shopify, Stripe, Supabase, Snowflake).
3. **Group C — Outreach Required**: Gated by partner certifications, commercial licensing, or enterprise sales reviews. Requires Composio business development outreach (e.g. Salesforce, DealCloud, Meta Ads, PitchBook).
4. **Group D — Further Investigation**: Blocked by Cloudflare WAF, unhosted portals, or missing documentation. Technical discovery must be conducted through private developer accounts or headless browser emulation.
5. **Group E — No Confirmed Path**: Confirmed local CLI binaries (Sherlock, Mermaid CLI) or consumer UI lacking standalone cloud REST APIs (NotebookLM).

### C. Multi-Label Authentication Co-Occurrence

Modern SaaS applications frequently offer multiple authentication mechanisms depending on user persona:
- **Machine-to-Machine / Developer**: API Key, Personal Access Token (PAT), Service Account.
- **User Delegation / Multi-Tenant**: OAuth 2.0 (Authorization Code + PKCE).

The analytics engine measures both individual method frequencies and cross-protocol co-occurrences without double-counting unique platforms in overall readiness totals.

---

## 11. Final Research Quality Audit & Dashboard Export Architecture (Prompt 10)

Before developing the web dashboard, the research dataset underwent a complete coverage and field-level quality audit (`scripts/prepare_dashboard_data.py`):

### A. Coverage Audit Criteria
- **100 Unique Applications**: Strictly IDs 1 to 100, verified against original assignment names and categories.
- **Categorical Integrity**: Exactly 10 applications per category across 10 categories.
- **Operational Status Distinction**:
  - `total_assigned`: 100
  - `research_attempted`: 100
  - `research_completed_passed`: 39
  - `research_partially_completed`: 22
  - `research_needs_review_blocked`: 39
  - `evidence_backed_rate`: 61.0% (61 platforms with verified documentation links).

### B. Field & Evidence Audit
- **16 Canonical Fields**: Audited across all 100 applications to verify that unknown values are strictly preserved without negative hallucinations.
- **4-Tier Evidence Quality Hierarchy**:
  - Level A: Source URL available (175 sources)
  - Level B: Source content successfully retrieved with HTTP 200 (87 sources)
  - Level C: Atomic claim supported by extracted excerpt (92 claim citations)
  - Level D: Independently corroborated (20 sampled applications cross-checked)

### C. Machine-Readable Dashboard Exports
Data is versioned and exported into `web/public/data/` adhering to strict TypeScript contracts defined in `docs/frontend_data_contract.md`:
- `apps.json`: 100 application objects with sanitized descriptions, bounded excerpts ($\le 280$ chars), and zero exposed secrets.
- `summary.json`, `categories.json`, `insights.json`, `verification.json`, `opportunities.json`.
- Validated via 10 automated integrity checks in `scripts/validate_dashboard_data.py`.
