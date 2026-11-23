# Frontend Data Contracts & Schema Specification

This document defines the strict machine-readable contracts for all JSON datasets exported to `web/public/data/` for the Composio AI Product Operations Case Study web application.

---

## 1. Overview of Dashboard Datasets

| File Path | Entity Represented | Record Count | Description |
|:---|:---|:---:|:---|
| `web/public/data/apps.json` | Applications | 100 | Full application research records, classification fields, evidence, and scores. |
| `web/public/data/summary.json` | Global KPIs & Distributions | 1 | Global dashboard KPIs, multi-label distributions, and verification funnel. |
| `web/public/data/categories.json` | Category Matrix | 10 | 10-category comparative benchmarks, rates, and dominant auth methods. |
| `web/public/data/insights.json` | Executive Strategic Insights | 5 | 5 evidence-backed strategic insights with metrics, denominators, and limits. |
| `web/public/data/verification.json`| Verification & Audit State | 1 | Funnel progression, correction history, and ground-truth audit state. |
| `web/public/data/opportunities.json`| Opportunities & Outreach | 1 | Top 10 opportunities, vendor outreach candidates, and group definitions. |

---

## 2. Dataset Schemas

### A. `apps.json` (Application Record Schema)

Array of 100 JSON objects. Each object conforms to:

```typescript
interface ApplicationRecord {
  app_id: number;                          // 1 to 100 (unique, strictly sequential)
  app_name: string;                        // Canonical name matching apps.json
  category_name: string;                   // 1 of 10 assigned categories
  category_slug: string;                   // URL-safe snake_case category identifier
  description: string;                     // Concise overview of product integration surface
  auth_methods: string[];                  // Allowed values or ["unknown"]
  credential_accessibility: string;        // 1 of 10 credential accessibility tiers
  credential_requirements: string[];       // Specific requirements (e.g. ["Paid Plan"])
  api_type: string[];                      // Protocols: ["REST"], ["GraphQL"], etc.
  api_breadth: string;                     // "extensive" | "broad" | "moderate" | "narrow" | "unknown"
  mcp_status: string;                      // "official_mcp" | "community_mcp" | "mcp_in_progress" | "mcp_unverified" | "unknown"
  mcp_repository_url: string | null;       // Verified GitHub repo URL or null
  buildability_verdict: string;            // "ready_to_build" | "feasible" | "needs_investigation" | "significant_barriers" | "not_feasible"
  toolkit_buildability_score: number;      // 1 to 10 integer scale
  priority_score: number;                  // 0 to 100 explainable priority score
  priority_status: string;                 // "SCORED" | "PROVISIONAL_LOW_EVIDENCE"
  opportunity_group: string;               // "Group A (Quick Wins)" | "Group B (Conditional)" | "Group C (Outreach Required)" | "Group D (Further Investigation)" | "Group E (No Confirmed Cloud Path)"
  primary_blocker: string;                 // Specific obstacle or "None identified"
  quality_gate_status: string;             // "passed" | "partial" | "needs_review" | "blocked"
  confidence: string;                      // "high" | "medium" | "low"
  evidence_count: number;                  // Number of verified evidence links
  evidence_links: EvidenceLink[];          // Structured citation objects
  research_status: string;                 // "completed_passed" | "partially_completed" | "needs_review"
  verification_status: string;             // "verified_passed" | "verified_partial" | "needs_investigation"
  last_researched_at: string;              // ISO 8601 UTC timestamp
}

interface EvidenceLink {
  url: string;                             // Valid HTTP/HTTPS documentation URL
  title: string;                           // Document title or anchor heading
  source_type: string;                     // "api_reference" | "official_documentation" | "developer_portal" | "mcp_registry"
  excerpt: string;                         // Verified citation excerpt (max 280 chars)
  claim_field: string;                     // "auth_methods" | "api_type" | "general"
}
```

### B. `summary.json` (Global KPIs & Distributions)

```typescript
interface SummaryData {
  meta: {
    title: string;
    version: string;
    generated_at: string;
    scope: string;
    accuracy_checkpoint: string;
  };
  kpis: {
    total_assigned_apps: number;           // 100
    total_researched_apps: number;         // 100
    evidence_backed_apps: number;          // 61
    evidence_backed_rate: string;          // "61.0%"
    quality_gate_passed: number;           // 39
    quality_gate_partial: number;          // 22
    quality_gate_needs_review: number;     // 39
    ready_to_build_count: number;          // 11
    feasible_count: number;                // 25
    needs_investigation_count: number;     // 60
    significant_barriers_count: number;    // 4
    dominant_auth_method: string;          // "OAuth 2.0 (73.9% of documented flows)"
    mcp_greenfield_rate: string;           // "92.0%"
    human_audit_status: string;            // "HUMAN AUDIT PENDING — ACCURACY NOT YET MEASURED"
    measured_accuracy: number | null;      // null (strict honesty guarantee)
  };
  distributions: {
    authentication_methods: Record<string, number>;
    credential_accessibility: Record<string, number>;
    api_breadth: Record<string, number>;
    mcp_status: Record<string, number>;
    buildability_verdicts: Record<string, number>;
    opportunity_groups: Record<string, number>;
  };
  funnel: {
    assigned: number;                      // 100
    attempted: number;                     // 100
    passing_validation: number;            // 100
    passing_quality_gates: number;         // 39
    partial_evidence: number;              // 22
    blocked_or_needs_review: number;       // 39
    independently_cross_checked: number;   // 20
    human_audited: number;                 // 0
  };
}
```

### C. `categories.json` (Category Comparison Matrix)

Dictionary keyed by canonical category name:

```typescript
type CategoriesData = Record<string, CategorySummary>;

interface CategorySummary {
  category_name: string;
  category_slug: string;
  assigned_apps: number;                   // 10
  quality_gate_passed: number;
  quality_gate_partial: number;
  quality_gate_needs_review: number;
  completeness_rate: string;               // e.g. "70.0%"
  average_buildability_score: number;      // e.g. 6.8
  confirmed_rest_count: number;
  confirmed_graphql_count: number;
  confirmed_mcp_count: number;
  ready_to_build_count: number;
  conditional_count: number;
  dominant_auth: string;
  app_ids: number[];                       // Exactly 10 app IDs
}
```

### D. `insights.json` (Executive Insights)

Array of 5 insight objects:

```typescript
interface ExecutiveInsight {
  insight_id: string;                      // "INSIGHT-01" to "INSIGHT-05"
  headline: string;                        // Concise strategic takeaway
  explanation: string;                     // Detailed operational finding
  metric: string;                          // e.g. "70.0% Quality Gate Pass Rate"
  denominator: string;                     // e.g. "10 Category Applications"
  supporting_apps: string[];               // Exemplary platforms
  evidence_reference: string;              // Exact data file source
  limitation: string;                      // Explicit operational or technical boundary
}
```

### E. `verification.json` (Verification & Ground-Truth State)

```typescript
interface VerificationData {
  status: string;                          // "HUMAN AUDIT PENDING — ACCURACY NOT YET MEASURED"
  human_audit: {
    complete: boolean;                     // false
    sample_size: number;                   // 20
    sample_seed: number;                   // 20261123
    measured_accuracy: number | null;      // null
    honesty_notice: string;                // Explicit honesty statement
  };
  corrections: {
    total_proposed_corrections: number;    // 3
    total_applied_corrections: number;     // 3
    corrections_independently_corroborated: number;
    corrections_awaiting_human_review: number;
    unresolved_contradictions: number;
    regressions_identified: number;
    applied_corrections: Array<{
      app_id: number;
      app_name: string;
      field_name: string;
      original_value: string;
      corrected_value: string;
      reason: string;
      timestamp: string;
      corroborated: boolean;
    }>;
    first_pass_snapshots_preserved: boolean; // true
  };
  automated_cross_checks: {
    total_sampled_apps: number;            // 20
    corroborated_with_secondary_sources: number;
    discrepancies_detected: number;
  };
  quality_gate_breakdown: {
    passed: number;
    partial: number;
    needs_review: number;
  };
}
```

### F. `opportunities.json` (Top Opportunities & Outreach Candidates)

```typescript
interface OpportunitiesData {
  top_10_opportunities: Array<{
    app_id: number;
    app_name: string;
    category: string;
    priority_score: number;
    toolkit_buildability_score: number;
    auth_methods: string[];
    credential_accessibility: string;
    api_surface: string[];
    api_breadth: string;
    mcp_status: string;
    main_reason: string;
    remaining_risk: string;
    supporting_documentation_urls: string[];
    verification_status: string;
  }>;
  vendor_outreach_candidates: Array<{
    app_id: number;
    app_name: string;
    category: string;
    confirmed_access_restriction: string;
    required_approval_or_commercial_step: string;
    technical_feasibility: string;
    evidence_urls: string[];
    suggested_action: string;
  }>;
  opportunity_group_definitions: Record<string, string>;
  opportunity_groups_distribution: Record<string, number>;
}
```

---

## 3. Allowed Enumerations & Taxonomies

| Dimension | Allowed Values |
|:---|:---|
| **`auth_methods`** | `"OAuth2"`, `"API Key"`, `"Bearer Token"`, `"Personal Access Token"`, `"Basic Auth"`, `"Service Account"`, `"JWT"`, `"HMAC"`, `"Session Based"`, `"Custom"`, `"unknown"` |
| **`credential_accessibility`** | `"free_self_serve"`, `"trial_self_serve"`, `"paid_self_serve"`, `"admin_approval"`, `"app_review_required"`, `"partner_approval"`, `"contact_sales"`, `"enterprise_only"`, `"no_hosted_credentials"`, `"unknown"` |
| **`api_breadth`** | `"extensive"`, `"broad"`, `"moderate"`, `"narrow"`, `"unknown"` |
| **`mcp_status`** | `"official_mcp"`, `"community_mcp"`, `"mcp_in_progress"`, `"mcp_unverified"`, `"unknown"` |
| **`buildability_verdict`** | `"ready_to_build"`, `"feasible"`, `"needs_investigation"`, `"significant_barriers"`, `"not_feasible"` |
| **`quality_gate_status`** | `"passed"`, `"partial"`, `"needs_review"`, `"blocked"` |
| **`confidence`** | `"high"`, `"medium"`, `"low"` |

---

## 4. Null and Unknown Handling Principles

1. **No Negative Hallucinations**: Missing or blocked documentation defaults strictly to `"unknown"` or `[]`. Inaccessibility does not imply that an API does not exist.
2. **Nullable Fields**: Only `mcp_repository_url` and `measured_accuracy` are permitted to be `null`.
3. **Array Fields**: `auth_methods`, `api_type`, and `credential_requirements` must always be arrays (empty `[]` or populated), never null.
4. **Number Formatting**: All floating-point scores are rounded to 1 decimal place. Integer scores (`app_id`, `priority_score`, `toolkit_buildability_score`) are strict integers.
5. **Security Guarantee**: No raw auth tokens, client secrets, passwords, or session cookies are present in any exported file. Excerpts are bounded to 280 characters.
