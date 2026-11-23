# Verification Case Studies & Error Provenance

## Overview

This document analyzes genuine empirical error modes, detection patterns, and correction lifecycles observed during the automated research of 100 applications. Every case study below is drawn directly from pipeline execution logs, first-pass snapshots (`data/batch1_first_pass.json`, `data/batch2_first_pass.json`), and the verification correction log (`data/correction_log.json`).

---

## Case Study 1: Correct Initially (High-Confidence Primary Grounding)

### Application: GitHub (App ID 61)
- **Category**: Developer, Infra and Data Platforms
- **First-Pass Answer**:
  - Auth: `OAuth2`
  - API Surface: `REST`, `GraphQL`
  - API Breadth: `extensive` (12+ endpoints)
  - MCP Status: `official_mcp` (`https://github.com/github` MCP server)
  - Buildability Score: 10 / 10 (`ready_to_build`)
  - Quality Gate: `passed`
- **Verification Evidence**:
  - Primary source (`https://docs.github.com/rest`) confirmed REST endpoints and OAuth scopes.
  - Secondary source (`https://github.com/github`) confirmed official vendor repository.
- **Verification Outcome**: `corroborated_by_independent_source`
- **Lesson**: Well-structured developer documentation with both cloud API documentation and public GitHub repositories provides the highest automated grounding rate.

---

## Case Study 2: Missed Authentication Method (Subpage Segregation)

### Application: Google Ads (App ID 31)
- **Category**: Marketing, Ads, Email and Social
- **First-Pass Answer**:
  - Auth: `[]` (Missed)
  - API Surface: `[]` (Missed)
  - Buildability Score: 5 / 10
  - Quality Gate: `partial`
- **Error Mechanism**:
  - Google Ads hosts its technical REST reference on `developers.google.com/google-ads/api/rest`, but all OAuth2 client credential and Service Account documentation is segregated under `developers.google.com/google-ads/api/docs/oauth`.
- **Evidence Found**:
  - Retrieved OAuth guide deep-link containing client ID, client secret, refresh token, and Service Account delegation flows.
- **Corrected Answer**:
  - Auth: `OAuth2`, `Service Account`
  - API Surface: `REST`
  - Buildability Score: 9 / 10 (`ready_to_build`)
  - Quality Gate: `passed`
- **Verification Status**: `verified_by_primary_source`
- **Lesson**: Large enterprise APIs split architecture over multiple subdomains; single-URL scraping produces false negatives unless accompanied by targeted authentication subpath discovery.

---

## Case Study 3: Contradicted MCP Claim (Community vs Official Repository)

### Application: Apify (App ID 55)
- **Category**: Data, SEO and Scraping
- **First-Pass Answer**:
  - MCP Status: `mcp_unverified`
  - Quality Gate: `passed`
- **Error Mechanism**:
  - Initial extraction flagged Apify MCP as `passed` quality gate despite MCP registry presence being unverified against an official Apify vendor repository.
- **Verification Evidence**:
  - Layer 3 contradiction check detected that community MCP servers exist in GitHub search results, but official vendor governance was not verified.
- **Corrected Answer**:
  - Quality Gate: Demoted from `passed` to `partial` (logged in `data/correction_log.json`).
  - MCP Status: Preserved as `mcp_unverified`.
- **Verification Status**: `needs_human_review`
- **Lesson**: Automated agents must never elevate community or third-party MCP servers to official status without cryptographic or organization-level proof.

---

## Case Study 4: Cloudflare WAF 403 Challenge Wall (Inaccessible Source)

### Application: Salesforce (App ID 1)
- **Category**: CRM and Sales
- **First-Pass Answer**:
  - Auth: `[]` (unknown)
  - API Surface: `[]` (unknown)
  - Quality Gate: `needs_review`
- **Error Mechanism**:
  - Standard HTTP fetcher requests to `developer.salesforce.com` and `developers.salesforce.com` were challenged and blocked with HTTP 403 Forbidden by Cloudflare Edge WAF.
- **Verification Evidence**:
  - Pipeline confirmed 4 attempts returning HTTP 403. Content validity detector classified the payload as anti-bot challenge wall.
- **Handling**:
  - Refused to hallucinate REST API endpoints or OAuth flows despite Salesforce being a well-known CRM.
  - Kept fields as `unknown`.
  - Quality Gate strictly assigned to `needs_review`.
- **Verification Status**: `source_unavailable`
- **Lesson**: Honest AI agents must prioritize reporting actual retrieval boundaries over superficial completeness.

---

## Case Study 5: Nonstandard Application Surface (CLI vs Cloud REST API)

### Application: Mermaid CLI (App ID 98)
- **Category**: AI, Research and Media-Native
- **First-Pass Answer**:
  - Auth: `[]` (unknown)
  - API Surface: `[]` (unknown)
  - Quality Gate: `needs_review`
- **Error Mechanism**:
  - Mermaid CLI (`@mermaid-js/mermaid-cli`) is a Node.js CLI tool running `mmdc` locally to compile diagram markdown into SVG/PNG. It has no hosted HTTP REST endpoints.
- **Cross-Check Evidence**:
  - GitHub repository (`github.com/mermaid-js/mermaid-cli`) confirmed package-based local execution.
- **Audit Recommendation**:
  - Categorized as `Local/Open-Source` CLI integration rather than forcing it into a cloud SaaS paradigm.
- **Verification Status**: `corroborated_nonstandard`
- **Lesson**: Research agents must support non-REST integration archetypes (CLI, SDK-only, Local OSS) to avoid misclassifying developer tools.

---

## Case Study 6: Enterprise-Gated Documentation (Private Client Login)

### Application: DealCloud (App ID 10)
- **Category**: CRM and Sales
- **First-Pass Answer**:
  - Auth: `[]`
  - API Surface: `[]`
  - Quality Gate: `needs_review`
- **Error Mechanism**:
  - DealCloud (an Intapp company) provides investment banking CRM software. Its developer portal (`developer.dealcloud.com`) does not exist publicly; API access is restricted behind signed client Master Service Agreements (MSAs) and private tenant logins.
- **Verification Outcome**:
  - Automated verifier flagged as `unresolved_enterprise_gated`.
  - Added to `data/human_audit_queue.json` for human partner outreach verification.
- **Verification Status**: `needs_human_review`
- **Lesson**: Distinguishing between an undocumented API and an enterprise-gated API requires tracking business onboarding models, not just HTTP status codes.

---

## Summary of Verification Loops

| App ID | Application | Initial Finding | Detected Defect | Verification Action | Final Gate |
|:---:|:---|:---|:---|:---|:---:|
| 1 | **Salesforce** | Score 4 | WAF 403 Forbidden | Preserved unknown, refused to guess | `needs_review` |
| 11 | **Zendesk** | Score 5 (missing API) | Subdomain restructure | Linked API basics guide, score -> 10 | `passed` |
| 31 | **Google Ads** | Score 5 (missing auth) | Subpage separation | Linked OAuth guide, score -> 9 | `passed` |
| 43 | **BigCommerce** | Gate `passed` | Unextracted auth | Demoted gate to `partial` in log | `partial` |
| 55 | **Apify** | Gate `passed` | Unverified MCP | Demoted gate to `partial` in log | `partial` |
| 58 | **Sherlock** | Score 4 | Local CLI tool | Flagged nonstandard surface | `needs_review` |
| 65 | **Supabase** | Gate `passed` | Unextracted auth | Demoted gate to `partial` in log | `partial` |
| 98 | **Mermaid CLI**| Score 4 | Local npm binary | Flagged nonstandard surface | `needs_review` |
