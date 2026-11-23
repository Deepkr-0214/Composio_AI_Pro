"""
Data models and schemas for the research agent.

Defines the structure of research findings with clear distinction
between unknown findings (not yet researched) and confirmed negatives
(researched and confirmed absent/unsupported).

Prompt 3 additions:
- MCPStatus enum (5 categories)
- BuildabilityVerdict enum (5 tiers)
- BlockerType enum (12+ blocker types)
- Expanded AuthMethod, CredentialAccessibility
- Claim-level evidence fields in ResearchFinding
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Any
import json


class FindingStatus(str, Enum):
    """
    Distinguishes between unknown findings and confirmed negatives.

    - UNKNOWN: Not yet researched or insufficient data to determine.
    - CONFIRMED_YES: Researched and confirmed to be true/present.
    - CONFIRMED_NO: Researched and confirmed to be false/absent.
    - PARTIAL: Partially supported or limited implementation.
    """
    UNKNOWN = "unknown"
    CONFIRMED_YES = "confirmed_yes"
    CONFIRMED_NO = "confirmed_no"
    PARTIAL = "partial"


class APIType(str, Enum):
    """Types of APIs an application may offer."""
    REST = "REST"
    GRAPHQL = "GraphQL"
    GRPC = "gRPC"
    SOAP = "SOAP"
    WEBSOCKET = "WebSocket"
    WEBHOOK = "Webhook"
    SDK_ONLY = "SDK Only"
    CLI_ONLY = "CLI Only"
    LOCAL_OSS = "Local/Open-Source"
    UNKNOWN = "unknown"
    NONE = "none"


class AuthMethod(str, Enum):
    """Authentication methods used by APIs."""
    OAUTH2 = "OAuth2"
    API_KEY = "API Key"
    BASIC_AUTH = "Basic Auth"
    BEARER_TOKEN = "Bearer Token"
    PERSONAL_ACCESS_TOKEN = "Personal Access Token"
    SERVICE_ACCOUNT = "Service Account"
    JWT = "JWT"
    HMAC = "HMAC"
    SESSION_BASED = "Session Based"
    CUSTOM = "Custom"
    UNKNOWN = "unknown"
    NONE = "none"


class ConfidenceLevel(str, Enum):
    """Confidence in the accuracy of research findings."""
    HIGH = "high"        # Verified from official documentation
    MEDIUM = "medium"    # From reliable secondary sources
    LOW = "low"          # Inferred or from unreliable sources
    UNVERIFIED = "unverified"  # Not yet verified


class APIBreadth(str, Enum):
    """How comprehensive the API coverage is."""
    EXTENSIVE = "extensive"      # Large multi-domain API surface
    BROAD = "broad"              # Many documented resources & CRUD
    MODERATE = "moderate"        # Several useful resources & workflows
    NARROW = "narrow"            # Limited documented operations
    UNKNOWN = "unknown"
    # Legacy aliases kept for backward compat
    COMPREHENSIVE = "comprehensive"
    LIMITED = "limited"
    MINIMAL = "minimal"


class CredentialAccessibility(str, Enum):
    """How easy it is to obtain API credentials."""
    FREE_SELF_SERVE = "free_self_serve"              # Free, instant signup
    TRIAL_SELF_SERVE = "trial_self_serve"             # Free trial, instant
    PAID_SELF_SERVE = "paid_self_serve"               # Paid, instant access
    ADMIN_APPROVAL = "admin_approval"                # Needs org admin approval
    APP_REVIEW_REQUIRED = "app_review_required"       # App review by vendor
    PARTNER_APPROVAL = "partner_approval"            # Partner program required
    CONTACT_SALES = "contact_sales"                  # Must contact sales
    ENTERPRISE_ONLY = "enterprise_only"              # Enterprise contracts only
    NO_HOSTED_CREDENTIALS = "no_hosted_credentials"  # OSS / local only
    UNKNOWN = "unknown"
    # Legacy aliases
    FREE_APPROVAL = "free_approval"
    PAID_APPROVAL = "paid_approval"
    PARTNER_ONLY = "partner_only"


class MCPStatus(str, Enum):
    """MCP (Model Context Protocol) server availability."""
    OFFICIAL = "official_mcp"              # Vendor-maintained MCP server
    COMMUNITY = "community_mcp"            # Community-maintained MCP server
    IN_PROGRESS = "mcp_in_progress"        # MCP server under development
    UNVERIFIED_CLAIM = "mcp_unverified"    # MCP mentioned but not verified
    UNKNOWN = "unknown"                    # No evidence found


class BuildabilityVerdict(str, Enum):
    """
    How feasible it is to build an AI agent toolkit for this application.
    """
    READY_TO_BUILD = "ready_to_build"              # Score 8-10
    FEASIBLE = "feasible"                          # Score 6-7
    NEEDS_INVESTIGATION = "needs_investigation"    # Score 4-5
    SIGNIFICANT_BARRIERS = "significant_barriers"  # Score 2-3
    NOT_FEASIBLE = "not_feasible"                  # Score 1
    UNKNOWN = "unknown"


class QualityGateStatus(str, Enum):
    """Research quality gate evaluation status."""
    PASSED = "passed"              # All gates passed, reliable evidence
    PARTIAL = "partial"            # Incomplete findings, some gaps
    NEEDS_REVIEW = "needs_review"  # Discrepancies, contradictions, or missing links
    BLOCKED = "blocked"            # Confirmed no API, paywalled, or blocked access


class BlockerType(str, Enum):
    """Types of blockers that prevent toolkit buildability."""
    NO_PUBLIC_API = "no_public_api"
    DEPRECATED_API = "deprecated_api"
    UNDOCUMENTED_API = "undocumented_api"
    CREDENTIAL_BARRIER = "credential_barrier"
    PARTNER_ONLY_ACCESS = "partner_only_access"
    ENTERPRISE_ONLY_ACCESS = "enterprise_only_access"
    RATE_LIMIT_TOO_STRICT = "rate_limit_too_strict"
    NO_SANDBOX = "no_sandbox"
    LEGAL_RESTRICTION = "legal_restriction"
    UNSTABLE_API = "unstable_api"
    MISSING_DOCUMENTATION = "missing_documentation"
    COMPLEX_AUTH = "complex_auth"


class VerificationStatus(str, Enum):
    """
    Verification statuses for claim-level and finding-level evidence (Prompt 7).
    """
    VERIFIED_BY_PRIMARY = "verified_by_primary_source"
    CORROBORATED_BY_INDEPENDENT = "corroborated_by_independent_source"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"
    SOURCE_UNAVAILABLE = "source_unavailable"
    NOT_CHECKED = "not_checked"


@dataclass
class EvidenceLink:
    """A URL with metadata supporting a research claim."""
    url: str
    title: str
    source_type: str  # e.g., "official_docs", "blog", "github", "community"
    accessed_date: str = ""
    notes: str = ""


@dataclass
class ClaimEvidence:
    """
    Evidence for a single research claim (Prompt 3).

    Each extracted field gets a list of these linking the claim
    to specific source URLs, excerpts, and confidence.
    """
    claim_field: str = ""       # e.g., "auth_methods", "api_type"
    claim_value: str = ""       # e.g., "OAuth2", "REST"
    source_url: str = ""
    source_title: str = ""
    supporting_excerpt: str = ""
    retrieved_at: str = ""
    confidence: str = ConfidenceLevel.MEDIUM.value
    verification_status: str = "unverified"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResearchFinding:
    """
    Complete research finding for a single application.

    Every field uses FindingStatus to distinguish between:
    - 'unknown': We haven't researched this yet.
    - 'confirmed_yes'/'confirmed_no': We researched and have an answer.
    - 'partial': Feature exists but with limitations.
    """
    # Identity
    app_id: int = 0
    app_name: str = ""
    category_id: int = 0
    category_name: str = ""

    # Core description
    description: str = ""
    website_url: str = ""

    # Authentication
    auth_methods: list[str] = field(default_factory=list)
    auth_methods_status: str = FindingStatus.UNKNOWN.value

    # Credential accessibility
    credential_accessibility: str = CredentialAccessibility.UNKNOWN.value
    credential_accessibility_status: str = FindingStatus.UNKNOWN.value
    credential_notes: str = ""

    # API information
    api_type: list[str] = field(default_factory=list)
    api_type_status: str = FindingStatus.UNKNOWN.value
    api_docs_url: str = ""

    # API breadth
    api_breadth: str = APIBreadth.UNKNOWN.value
    api_breadth_status: str = FindingStatus.UNKNOWN.value
    api_breadth_notes: str = ""
    estimated_endpoint_count: Optional[int] = None

    # MCP support (Prompt 3 expanded)
    has_official_mcp: str = FindingStatus.UNKNOWN.value
    has_community_mcp: str = FindingStatus.UNKNOWN.value
    mcp_status: str = MCPStatus.UNKNOWN.value
    mcp_repo_url: str = ""
    mcp_notes: str = ""

    # Toolkit / integration buildability (Prompt 3 expanded)
    toolkit_buildability: str = FindingStatus.UNKNOWN.value
    toolkit_buildability_score: Optional[int] = None  # 1-10 scale
    toolkit_buildability_notes: str = ""
    buildability_verdict: str = BuildabilityVerdict.UNKNOWN.value

    # Blockers and challenges
    blockers: list[str] = field(default_factory=list)
    blockers_status: str = FindingStatus.UNKNOWN.value

    # Overall confidence
    overall_confidence: str = ConfidenceLevel.UNVERIFIED.value

    # Evidence
    evidence_links: list[dict] = field(default_factory=list)
    claim_evidence: list[dict] = field(default_factory=list)  # Prompt 3: per-claim evidence

    # Evidence quality (Prompt 3 & 4)
    evidence_quality_score: Optional[float] = None
    evidence_warnings: list[str] = field(default_factory=list)
    quality_gate_status: str = QualityGateStatus.NEEDS_REVIEW.value
    quality_gate_checks: dict = field(default_factory=dict)

    # Research metadata
    researched_at: str = ""
    verified_at: str = ""
    research_notes: str = ""
    research_duration_seconds: Optional[float] = None  # Prompt 3: per-app timing
    human_intervention_needed: bool = False
    human_intervention_notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchFinding":
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class VerificationResult:
    """Result of verifying a single research finding or claim (Prompt 7)."""
    app_id: int = 0
    app_name: str = ""
    field_verified: str = ""
    original_value: Any = None
    verified_value: Any = None
    is_accurate: bool = False
    confidence: str = ConfidenceLevel.UNVERIFIED.value
    verification_method: str = ""
    verification_status: str = VerificationStatus.NOT_CHECKED.value
    source_urls: list[str] = field(default_factory=list)
    additional_evidence: Any = None
    contradictions: list[str] = field(default_factory=list)
    recommended_correction: Any = None
    reviewer_type: str = "automated_verifier"
    verification_timestamp: str = ""
    verification_notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class CorrectionRecord:
    """Record of a safe automated or human correction (Prompt 7)."""
    app_id: int = 0
    app_name: str = ""
    field_name: str = ""
    original_value: Any = None
    corrected_value: Any = None
    reason_for_correction: str = ""
    original_evidence: Any = None
    new_evidence: Any = None
    correction_method: str = "automated_rule"
    correction_timestamp: str = ""
    whether_human_approval_is_required: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def create_empty_finding(app_id: int, app_name: str, category_id: int, category_name: str) -> ResearchFinding:
    """Create an empty research finding with all fields set to unknown."""
    return ResearchFinding(
        app_id=app_id,
        app_name=app_name,
        category_id=category_id,
        category_name=category_name,
    )
