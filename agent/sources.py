"""
Source discovery engine for the Composio research agent.

Automatically identifies reliable developer documentation for each
application using multiple search strategies and known URL patterns.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
SOURCES_FILE = DATA_DIR / "source_records.json"


# ---------------------------------------------------------------------------
# Enums & dataclasses
# ---------------------------------------------------------------------------


class SourceType(str, Enum):
    """Types of research sources."""
    OFFICIAL_DOCS = "official_documentation"
    API_REFERENCE = "api_reference"
    AUTH_DOCS = "authentication_documentation"
    DEVELOPER_PORTAL = "developer_portal"
    GITHUB_REPO = "github_repository"
    PRICING_PAGE = "pricing_page"
    MCP_REGISTRY = "mcp_registry"
    COMMUNITY_MCP = "community_mcp_repository"
    THIRD_PARTY = "third_party"
    CHANGELOG = "changelog"


class FetchStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"       # paywall / captcha / auth wall
    RATE_LIMITED = "rate_limited"


@dataclass
class SourceRecord:
    """
    A single discovered source for an application.
    Uses real values only after successful discovery or retrieval.
    """
    app_id: int
    app_name: str
    source_type: str                    # SourceType value
    source_url: Optional[str] = None
    final_url: Optional[str] = None     # after redirects
    source_title: Optional[str] = None
    retrieved_at: Optional[str] = None
    http_status: Optional[int] = None
    content_excerpt: Optional[str] = None
    content_hash: Optional[str] = None
    discovery_method: Optional[str] = None
    fetch_status: str = FetchStatus.PENDING.value
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SourceRecord":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ---------------------------------------------------------------------------
# Known documentation URL patterns (curated, NOT fabricated)
# ---------------------------------------------------------------------------

KNOWN_DOCS: dict[str, list[dict]] = {
    # --- CRM and Sales ---
    "salesforce": [
        {"url": "https://developer.salesforce.com/docs/apis", "type": SourceType.API_REFERENCE.value},
        {"url": "https://developer.salesforce.com/", "type": SourceType.DEVELOPER_PORTAL.value},
    ],
    "hubspot": [
        {"url": "https://developers.hubspot.com/docs/api/overview", "type": SourceType.API_REFERENCE.value},
        {"url": "https://developers.hubspot.com/", "type": SourceType.DEVELOPER_PORTAL.value},
    ],
    "pipedrive": [
        {"url": "https://developers.pipedrive.com/docs/api/v1", "type": SourceType.API_REFERENCE.value},
    ],
    "attio": [
        {"url": "https://developers.attio.com/reference", "type": SourceType.API_REFERENCE.value},
    ],
    "twenty": [
        {"url": "https://twenty.com/developers/rest-api", "type": SourceType.API_REFERENCE.value},
        {"url": "https://github.com/twentyhq/twenty", "type": SourceType.GITHUB_REPO.value},
    ],
    "podio": [
        {"url": "https://developers.podio.com/", "type": SourceType.DEVELOPER_PORTAL.value},
    ],
    "zoho crm": [
        {"url": "https://www.zoho.com/crm/developer/docs/api/v7/", "type": SourceType.API_REFERENCE.value},
    ],
    "close": [
        {"url": "https://developer.close.com/", "type": SourceType.API_REFERENCE.value},
    ],
    "copper": [
        {"url": "https://developer.copper.com/", "type": SourceType.API_REFERENCE.value},
    ],

    # --- Support & Helpdesk ---
    "zendesk": [
        {"url": "https://developer.zendesk.com/api-reference", "type": SourceType.API_REFERENCE.value},
        {"url": "https://developer.zendesk.com/documentation/api-basics/", "type": SourceType.AUTH_DOCS.value},
    ],
    "intercom": [
        {"url": "https://developers.intercom.com/docs/references/rest-api/api.intercom.io/", "type": SourceType.API_REFERENCE.value},
    ],
    "freshdesk": [
        {"url": "https://developers.freshdesk.com/api/", "type": SourceType.API_REFERENCE.value},
    ],
    "front": [
        {"url": "https://dev.frontapp.com/reference/introduction", "type": SourceType.API_REFERENCE.value},
    ],
    "help scout": [
        {"url": "https://developer.helpscout.com/", "type": SourceType.DEVELOPER_PORTAL.value},
    ],
    "gorgias": [
        {"url": "https://developers.gorgias.com/reference/introduction", "type": SourceType.API_REFERENCE.value},
    ],

    # --- Communications ---
    "slack": [
        {"url": "https://api.slack.com/", "type": SourceType.API_REFERENCE.value},
        {"url": "https://api.slack.com/authentication", "type": SourceType.AUTH_DOCS.value},
    ],
    "twilio": [
        {"url": "https://www.twilio.com/docs/usage/api", "type": SourceType.API_REFERENCE.value},
    ],
    "discord": [
        {"url": "https://discord.com/developers/docs/intro", "type": SourceType.API_REFERENCE.value},
    ],
    "telegram": [
        {"url": "https://core.telegram.org/bots/api", "type": SourceType.API_REFERENCE.value},
    ],
    "whatsapp business": [
        {"url": "https://developers.facebook.com/docs/whatsapp/cloud-api/", "type": SourceType.API_REFERENCE.value},
    ],
    "aircall": [
        {"url": "https://developer.aircall.io/api-references/", "type": SourceType.API_REFERENCE.value},
    ],
    "vonage": [
        {"url": "https://developer.vonage.com/en/api", "type": SourceType.API_REFERENCE.value},
    ],

    # --- Marketing ---
    "google ads": [
        {"url": "https://developers.google.com/google-ads/api/docs/start", "type": SourceType.API_REFERENCE.value},
        {"url": "https://developers.google.com/google-ads/api/docs/oauth/overview", "type": SourceType.AUTH_DOCS.value},
    ],
    "meta ads": [
        {"url": "https://developers.facebook.com/docs/marketing-apis/", "type": SourceType.API_REFERENCE.value},
    ],
    "linkedin ads": [
        {"url": "https://learn.microsoft.com/en-us/linkedin/marketing/", "type": SourceType.API_REFERENCE.value},
    ],
    "mailchimp": [
        {"url": "https://mailchimp.com/developer/marketing/api/", "type": SourceType.API_REFERENCE.value},
    ],
    "klaviyo": [
        {"url": "https://developers.klaviyo.com/en/reference/api_overview", "type": SourceType.API_REFERENCE.value},
    ],
    "pinterest": [
        {"url": "https://developers.pinterest.com/docs/api/v5/", "type": SourceType.API_REFERENCE.value},
    ],
    "sendgrid": [
        {"url": "https://docs.sendgrid.com/api-reference", "type": SourceType.API_REFERENCE.value},
    ],

    # --- Ecommerce ---
    "shopify": [
        {"url": "https://shopify.dev/docs/api", "type": SourceType.API_REFERENCE.value},
        {"url": "https://shopify.dev/docs/apps/build/authentication-authorization", "type": SourceType.AUTH_DOCS.value},
    ],
    "woocommerce": [
        {"url": "https://woocommerce.github.io/woocommerce-rest-api-docs/", "type": SourceType.API_REFERENCE.value},
        {"url": "https://github.com/woocommerce/woocommerce", "type": SourceType.GITHUB_REPO.value},
    ],
    "bigcommerce": [
        {"url": "https://developer.bigcommerce.com/docs/rest", "type": SourceType.API_REFERENCE.value},
    ],
    "magento (adobe commerce)": [
        {"url": "https://developer.adobe.com/commerce/webapi/rest/", "type": SourceType.API_REFERENCE.value},
    ],
    "squarespace": [
        {"url": "https://developers.squarespace.com/", "type": SourceType.DEVELOPER_PORTAL.value},
    ],
    "ecwid": [
        {"url": "https://api-docs.ecwid.com/reference/overview", "type": SourceType.API_REFERENCE.value},
    ],
    "gumroad": [
        {"url": "https://app.gumroad.com/api", "type": SourceType.API_REFERENCE.value},
    ],
    "amazon selling partner": [
        {"url": "https://developer-docs.amazon.com/sp-api/", "type": SourceType.API_REFERENCE.value},
    ],

    # --- Data, SEO & Scraping ---
    "dataforseo": [
        {"url": "https://docs.dataforseo.com/", "type": SourceType.API_REFERENCE.value},
    ],
    "ahrefs": [
        {"url": "https://ahrefs.com/api", "type": SourceType.API_REFERENCE.value},
    ],
    "apify": [
        {"url": "https://docs.apify.com/api/v2", "type": SourceType.API_REFERENCE.value},
        {"url": "https://github.com/apify", "type": SourceType.GITHUB_REPO.value},
    ],
    "firecrawl": [
        {"url": "https://docs.firecrawl.dev/api-reference/introduction", "type": SourceType.API_REFERENCE.value},
        {"url": "https://github.com/mendableai/firecrawl", "type": SourceType.GITHUB_REPO.value},
    ],
    "bright data": [
        {"url": "https://docs.brightdata.com/", "type": SourceType.API_REFERENCE.value},
    ],

    # --- Developer, Infra ---
    "github": [
        {"url": "https://docs.github.com/en/rest", "type": SourceType.API_REFERENCE.value},
        {"url": "https://docs.github.com/en/graphql", "type": SourceType.API_REFERENCE.value},
    ],
    "vercel": [
        {"url": "https://vercel.com/docs/rest-api", "type": SourceType.API_REFERENCE.value},
    ],
    "netlify": [
        {"url": "https://docs.netlify.com/api/get-started/", "type": SourceType.API_REFERENCE.value},
    ],
    "cloudflare": [
        {"url": "https://developers.cloudflare.com/api/", "type": SourceType.API_REFERENCE.value},
    ],
    "supabase": [
        {"url": "https://supabase.com/docs/guides/api", "type": SourceType.API_REFERENCE.value},
        {"url": "https://github.com/supabase/supabase", "type": SourceType.GITHUB_REPO.value},
    ],
    "neo4j": [
        {"url": "https://neo4j.com/docs/http-api/current/", "type": SourceType.API_REFERENCE.value},
    ],
    "snowflake": [
        {"url": "https://docs.snowflake.com/en/developer-guide/sql-api/index", "type": SourceType.API_REFERENCE.value},
    ],
    "mongodb atlas": [
        {"url": "https://www.mongodb.com/docs/atlas/api/", "type": SourceType.API_REFERENCE.value},
    ],
    "datadog": [
        {"url": "https://docs.datadoghq.com/api/latest/", "type": SourceType.API_REFERENCE.value},
    ],
    "sentry": [
        {"url": "https://docs.sentry.io/api/", "type": SourceType.API_REFERENCE.value},
        {"url": "https://github.com/getsentry/sentry", "type": SourceType.GITHUB_REPO.value},
    ],

    # --- Productivity ---
    "notion": [
        {"url": "https://developers.notion.com/reference/intro", "type": SourceType.API_REFERENCE.value},
    ],
    "airtable": [
        {"url": "https://airtable.com/developers/web/api/introduction", "type": SourceType.API_REFERENCE.value},
    ],
    "linear": [
        {"url": "https://developers.linear.app/docs/graphql/working-with-the-graphql-api", "type": SourceType.API_REFERENCE.value},
    ],
    "jira": [
        {"url": "https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/", "type": SourceType.API_REFERENCE.value},
    ],
    "asana": [
        {"url": "https://developers.asana.com/reference/rest-api-reference", "type": SourceType.API_REFERENCE.value},
    ],
    "monday.com": [
        {"url": "https://developer.monday.com/api-reference/reference/api-v2", "type": SourceType.API_REFERENCE.value},
    ],
    "clickup": [
        {"url": "https://clickup.com/api/", "type": SourceType.API_REFERENCE.value},
    ],
    "coda": [
        {"url": "https://coda.io/developers/apis/v1", "type": SourceType.API_REFERENCE.value},
    ],
    "smartsheet": [
        {"url": "https://smartsheet.redoc.ly/", "type": SourceType.API_REFERENCE.value},
    ],
    "harvest": [
        {"url": "https://help.getharvest.com/api-v2/", "type": SourceType.API_REFERENCE.value},
    ],

    # --- Finance ---
    "stripe": [
        {"url": "https://docs.stripe.com/api", "type": SourceType.API_REFERENCE.value},
    ],
    "plaid": [
        {"url": "https://plaid.com/docs/api/", "type": SourceType.API_REFERENCE.value},
    ],
    "binance": [
        {"url": "https://developers.binance.com/docs/binance-spot-api-docs/rest-api", "type": SourceType.API_REFERENCE.value},
    ],
    "quickbooks": [
        {"url": "https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/account", "type": SourceType.API_REFERENCE.value},
    ],
    "xero": [
        {"url": "https://developer.xero.com/documentation/api/accounting/overview", "type": SourceType.API_REFERENCE.value},
    ],
    "brex": [
        {"url": "https://developer.brex.com/", "type": SourceType.DEVELOPER_PORTAL.value},
    ],
    "ramp": [
        {"url": "https://docs.ramp.com/developer-api", "type": SourceType.API_REFERENCE.value},
    ],

    # --- AI, Research, Media-Native ---
    "devin": [
        {"url": "https://docs.devin.ai/", "type": SourceType.OFFICIAL_DOCS.value},
        {"url": "https://docs.devin.ai/api-reference", "type": SourceType.API_REFERENCE.value},
    ],
    "reducto": [
        {"url": "https://docs.reducto.ai/", "type": SourceType.API_REFERENCE.value},
    ],
    "grain": [
        {"url": "https://grain.com/", "type": SourceType.OFFICIAL_DOCS.value},
    ],
}


# ---------------------------------------------------------------------------
# Source discovery strategies
# ---------------------------------------------------------------------------


def _normalize_app_key(name: str) -> str:
    """Normalize app name for lookup in KNOWN_DOCS."""
    return name.strip().lower()


def discover_known_sources(app_id: int, app_name: str) -> list[SourceRecord]:
    """
    Discover sources from the curated KNOWN_DOCS map.
    Returns SourceRecords with fetch_status=pending.
    """
    key = _normalize_app_key(app_name)
    entries = KNOWN_DOCS.get(key, [])
    records: list[SourceRecord] = []
    for e in entries:
        records.append(SourceRecord(
            app_id=app_id,
            app_name=app_name,
            source_type=e["type"],
            source_url=e["url"],
            discovery_method="known_docs_map",
            fetch_status=FetchStatus.PENDING.value,
        ))
    return records


def build_candidate_urls(app_name: str) -> list[dict]:
    """
    Generate candidate documentation URLs from common patterns.
    These are *candidates* — they must be fetched to verify existence.
    """
    # Create slug variations
    slug = re.sub(r"[^a-z0-9]+", "-", app_name.lower()).strip("-")
    slug_nodash = slug.replace("-", "")
    # For names like "Zoho CRM" → "zoho"
    first_word = app_name.lower().split()[0] if app_name else ""

    candidates = []
    for base in [slug, slug_nodash, first_word]:
        if not base:
            continue
        candidates.extend([
            {"url": f"https://developers.{base}.com/", "type": SourceType.DEVELOPER_PORTAL.value},
            {"url": f"https://developer.{base}.com/", "type": SourceType.DEVELOPER_PORTAL.value},
            {"url": f"https://{base}.com/developers", "type": SourceType.DEVELOPER_PORTAL.value},
            {"url": f"https://docs.{base}.com/", "type": SourceType.OFFICIAL_DOCS.value},
            {"url": f"https://{base}.com/docs", "type": SourceType.OFFICIAL_DOCS.value},
            {"url": f"https://api.{base}.com/", "type": SourceType.API_REFERENCE.value},
            {"url": f"https://github.com/{base}", "type": SourceType.GITHUB_REPO.value},
        ])

    # Deduplicate by URL
    seen = set()
    unique = []
    for c in candidates:
        if c["url"] not in seen:
            seen.add(c["url"])
            unique.append(c)
    return unique


def build_mcp_search_urls(app_name: str) -> list[dict]:
    """
    Generate candidate URLs to discover MCP server availability.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", app_name.lower()).strip("-")
    return [
        {"url": f"https://github.com/search?q={slug}+mcp+server&type=repositories", "type": SourceType.MCP_REGISTRY.value},
        {"url": f"https://github.com/modelcontextprotocol/servers/tree/main/src/{slug}", "type": SourceType.MCP_REGISTRY.value},
    ]


def discover_all_candidate_sources(app_id: int, app_name: str) -> list[SourceRecord]:
    """
    Discover all candidate sources for an application:
    1. Known curated docs (high confidence)
    2. Generated candidate URLs (need verification)
    3. MCP search URLs (need verification)

    Returns SourceRecords with fetch_status=pending.
    """
    records: list[SourceRecord] = []
    seen_urls: set[str] = set()

    # 1. Known docs — highest priority
    for rec in discover_known_sources(app_id, app_name):
        if rec.source_url and rec.source_url not in seen_urls:
            seen_urls.add(rec.source_url)
            records.append(rec)

    # 2. Candidate URLs
    for c in build_candidate_urls(app_name):
        if c["url"] not in seen_urls:
            seen_urls.add(c["url"])
            records.append(SourceRecord(
                app_id=app_id,
                app_name=app_name,
                source_type=c["type"],
                source_url=c["url"],
                discovery_method="url_pattern_generation",
                fetch_status=FetchStatus.PENDING.value,
            ))

    # 3. MCP search
    for c in build_mcp_search_urls(app_name):
        if c["url"] not in seen_urls:
            seen_urls.add(c["url"])
            records.append(SourceRecord(
                app_id=app_id,
                app_name=app_name,
                source_type=c["type"],
                source_url=c["url"],
                discovery_method="mcp_search",
                fetch_status=FetchStatus.PENDING.value,
            ))

    return records


# ---------------------------------------------------------------------------
# Source record persistence
# ---------------------------------------------------------------------------


def load_source_records() -> list[dict]:
    """Load existing source records."""
    if SOURCES_FILE.exists():
        with open(SOURCES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    return []


def save_source_records(records: list[dict]) -> None:
    """Save source records to disk."""
    SOURCES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SOURCES_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def get_source_records_for_app(app_id: int) -> list[dict]:
    """Get all source records for a specific app."""
    all_records = load_source_records()
    return [r for r in all_records if r.get("app_id") == app_id]


def merge_source_records(existing: list[dict], new: list[dict]) -> list[dict]:
    """
    Merge new source records into existing, avoiding duplicates.
    Duplicates are identified by (app_id, source_url).
    """
    seen = {(r["app_id"], r.get("source_url")) for r in existing}
    merged = list(existing)
    for rec in new:
        key = (rec["app_id"], rec.get("source_url"))
        if key not in seen:
            seen.add(key)
            merged.append(rec)
    return merged


def content_hash(text: str) -> str:
    """SHA-256 hash of content for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def get_source_priority() -> list[str]:
    """
    Return source types in priority order for research.
    Official docs are always preferred over community sources.
    """
    return [
        SourceType.OFFICIAL_DOCS.value,
        SourceType.API_REFERENCE.value,
        SourceType.AUTH_DOCS.value,
        SourceType.DEVELOPER_PORTAL.value,
        SourceType.GITHUB_REPO.value,
        SourceType.PRICING_PAGE.value,
        SourceType.MCP_REGISTRY.value,
        SourceType.COMMUNITY_MCP.value,
        SourceType.CHANGELOG.value,
        SourceType.THIRD_PARTY.value,
    ]
