"""
CLI entry point for the Composio research agent.

Usage:
    python -m agent.research --limit 1
    python -m agent.research --limit 5
    python -m agent.research --category "CRM and Sales"
    python -m agent.research --app-id 61
    python -m agent.research --all
    python -m agent.research --progress
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Ensure parent is on path for relative imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.research import (
    research_apps,
    get_research_progress,
    load_apps,
    get_or_initialize_results,
    PILOT_APP_IDS,
    PILOT_CSV_FILE,
    save_pilot_first_pass,
    calculate_pilot_metrics,
    export_csv,
)


def setup_logging(level: str = "INFO") -> None:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_progress() -> None:
    progress = get_research_progress()
    print(f"\n{'='*50}")
    print(f"Research Progress")
    print(f"{'='*50}")
    print(f"  Total apps:         {progress['total']}")
    print(f"  Researched:         {progress['researched']}")
    print(f"  Verified:           {progress['verified']}")
    print(f"  % Researched:       {progress['percent_researched']}%")
    print(f"  % Verified:         {progress['percent_verified']}%")
    print(f"{'='*50}\n")


def list_categories() -> None:
    apps_data = load_apps()
    print("\nAvailable categories:")
    for cat in apps_data["categories"]:
        print(f"  [{cat['id']:2d}] {cat['name']}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Composio Research Agent — Investigate application APIs and integrations",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Maximum number of apps to research",
    )
    parser.add_argument(
        "--category", type=str, default=None,
        help="Research only apps in this category (e.g., 'CRM and Sales')",
    )
    parser.add_argument(
        "--app-id", type=int, nargs="+", default=None,
        help="Research specific app IDs",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Research all 100 applications",
    )
    parser.add_argument(
        "--pilot", action="store_true",
        help="Run 10-app pilot across all 10 categories",
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Re-research already completed apps",
    )
    parser.add_argument(
        "--concurrency", type=int, default=5,
        help="Max concurrent HTTP requests (default: 5)",
    )
    parser.add_argument(
        "--progress", action="store_true",
        help="Show research progress and exit",
    )
    parser.add_argument(
        "--list-categories", action="store_true",
        help="List available categories and exit",
    )
    parser.add_argument(
        "--log-level", type=str, default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()
    setup_logging(args.log_level)

    if args.progress:
        print_progress()
        return

    if args.list_categories:
        list_categories()
        return

    # Determine what to research
    if args.all:
        app_ids = None
        category = None
        limit = None
    elif args.pilot:
        app_ids = PILOT_APP_IDS
        category = None
        limit = None
    elif args.app_id:
        app_ids = args.app_id
        category = None
        limit = None
    elif args.category:
        app_ids = None
        category = args.category
        limit = args.limit
    elif args.limit:
        app_ids = None
        category = None
        limit = args.limit
    else:
        parser.print_help()
        print("\nUse --progress to check status, or specify --limit, --category, --app-id, or --all.")
        return

    skip_completed = not args.refresh

    # Run research
    print(f"\nStarting research...")
    if limit:
        print(f"  Limit: {limit} apps")
    if category:
        print(f"  Category: {category}")
    if app_ids:
        print(f"  App IDs: {app_ids}")
    print(f"  Concurrency: {args.concurrency}")
    print(f"  Skip completed: {skip_completed}")
    print()

    summary = asyncio.run(
        research_apps(
            app_ids=app_ids,
            category_name=category,
            limit=limit,
            skip_completed=skip_completed,
            concurrency=args.concurrency,
        )
    )

    # Print summary
    print(f"\n{'='*50}")
    print(f"Research Summary")
    print(f"{'='*50}")
    if "error" in summary:
        print(f"  ERROR: {summary['error']}")
    else:
        print(f"  Apps researched:        {summary.get('researched', 0)}")
        print(f"  Sources discovered:     {summary.get('total_sources_discovered', 0)}")
        print(f"  Total sources stored:   {summary.get('total_sources_stored', 0)}")
        if summary.get("errors"):
            print(f"  Errors:")
            for err in summary["errors"]:
                print(f"    - {err}")
        prog = summary.get("progress", {})
        if prog:
            print(f"  Overall progress:       {prog.get('researched', 0)}/{prog.get('total', 0)} "
                  f"({prog.get('percent_researched', 0)}%)")
    print(f"{'='*50}\n")

    # If pilot run, calculate and display pilot metrics
    if args.pilot:
        all_results = get_or_initialize_results()
        pilot_results = [r for r in all_results if r.get("app_id") in PILOT_APP_IDS]
        save_pilot_first_pass(pilot_results)
        export_csv(pilot_results, PILOT_CSV_FILE)
        metrics = calculate_pilot_metrics(pilot_results, concurrency=args.concurrency)
        print(f"{'='*50}")
        print(f"Pilot Quality & Operations Metrics (10 Applications)")
        print(f"{'='*50}")
        print(f"  Total Attempted:        {metrics.get('applications_attempted')}")
        print(f"  Passed Quality Gates:   {metrics.get('successfully_passed_quality_gates')}")
        print(f"  Partially Processed:    {metrics.get('partially_processed')}")
        print(f"  Needs Review:           {metrics.get('needs_review')}")
        print(f"  Blocked:                {metrics.get('blocked')}")
        print(f"  With Official Evidence: {metrics.get('with_official_documentation_evidence')}")
        print(f"  Missing Auth Evidence:  {metrics.get('missing_authentication_evidence')}")
        print(f"  Missing Creds Evidence: {metrics.get('missing_credential_access_evidence')}")
        print(f"  Unresolved MCP Status:  {metrics.get('unresolved_mcp_status')}")
        print(f"  Avg Duration Per App:   {metrics.get('average_duration_seconds_per_app')}s")
        print(f"  Est. 100-App Full Run:  {metrics.get('estimated_full_100_apps_minutes')} mins")
        print(f"{'='*50}\n")


if __name__ == "__main__":
    main()

