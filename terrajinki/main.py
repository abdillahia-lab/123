#!/usr/bin/env python3
"""
TerraJinki - The Spirit of Earth Energy

AI-powered renewable energy site intelligence platform.

Usage:
    python -m terrajinki.main serve      # Start API server
    python -m terrajinki.main analyze    # Analyze a site
    python -m terrajinki.main search     # Search parcels
"""

import argparse
import asyncio
import json
import logging
import sys
from typing import Optional

from terrajinki.core.config import get_config, TerraJinkiConfig, Environment
from terrajinki.core.engine import TerraJinkiEngine
from terrajinki.core.types import (
    Parcel,
    ProjectType,
    ZoningType,
    SolarPermission,
    GeoPoint,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("terrajinki")


def print_banner():
    """Print TerraJinki banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ████████╗███████╗██████╗ ██████╗  █████╗                   ║
║   ╚══██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗                  ║
║      ██║   █████╗  ██████╔╝██████╔╝███████║                  ║
║      ██║   ██╔══╝  ██╔══██╗██╔══██╗██╔══██║                  ║
║      ██║   ███████╗██║  ██║██║  ██║██║  ██║                  ║
║      ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝                  ║
║                                                              ║
║         ██╗██╗███╗   ██╗██╗  ██╗██╗                          ║
║         ██║██║████╗  ██║██║ ██╔╝██║                          ║
║         ██║██║██╔██╗ ██║█████╔╝ ██║                          ║
║    ██   ██║██║██║╚██╗██║██╔═██╗ ██║                          ║
║    ╚█████╔╝██║██║ ╚████║██║  ██╗██║                          ║
║     ╚════╝ ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝                          ║
║                                                              ║
║   The Spirit of Earth Energy                                 ║
║   AI-Powered Renewable Energy Site Intelligence              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def cmd_serve(args):
    """Start the API server."""
    import uvicorn
    from terrajinki.api.app import create_app

    config = get_config()
    app = create_app(config)

    print_banner()
    logger.info(f"Starting TerraJinki API server on {args.host}:{args.port}")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


def cmd_analyze(args):
    """Analyze a site."""
    async def run_analysis():
        print_banner()

        config = get_config()
        engine = TerraJinkiEngine(config)

        # Create sample parcel from args
        parcel = Parcel(
            state=args.state,
            county=args.county,
            acreage=args.acreage,
            zoning_type=ZoningType.AGRICULTURAL,
            solar_permission=SolarPermission.UNKNOWN,
            centroid=GeoPoint(
                latitude=args.latitude or 30.0,
                longitude=args.longitude or -95.0,
            ),
            nearest_substation_mi=args.substation_distance,
        )

        # Register parcel
        parcel = await engine.create_parcel(parcel)

        logger.info(f"Analyzing parcel in {args.county}, {args.state} ({args.acreage} acres)")

        try:
            project_type = ProjectType(args.project_type)
        except ValueError:
            project_type = ProjectType.UTILITY_SOLAR

        # Run analysis
        analysis = await engine.analyze_site(
            parcel=parcel,
            project_type=project_type,
        )

        # Print results
        print("\n" + "=" * 60)
        print("SITE ANALYSIS RESULTS")
        print("=" * 60)

        if analysis.score:
            score = analysis.score
            print(f"\nOverall Score: {score.overall_score:.1f}/100 ({score.viability})")
            print(f"Star Rating: {'⭐' * score.star_rating}")
            print(f"\nComponent Scores:")
            print(f"  Permitting:    {score.permitting_score:.1f}/100")
            print(f"  Grid:          {score.grid_score:.1f}/100")
            print(f"  Environmental: {score.environmental_score:.1f}/100")
            print(f"  Land:          {score.land_score:.1f}/100")

            if score.fatal_flaws:
                print(f"\n⚠️  FATAL FLAWS:")
                for flaw in score.fatal_flaws:
                    print(f"  - {flaw}")

            if score.major_risks:
                print(f"\n⚠️  Major Risks:")
                for risk in score.major_risks[:5]:
                    print(f"  - {risk}")

        print(f"\nRecommendation: {analysis.proceed_recommendation}")

        if analysis.recommended_next_steps:
            print(f"\nRecommended Next Steps:")
            for i, step in enumerate(analysis.recommended_next_steps[:5], 1):
                print(f"  {i}. {step}")

        print(f"\nAnalysis completed in {analysis.duration_seconds:.1f} seconds")
        print("=" * 60)

    asyncio.run(run_analysis())


def cmd_search(args):
    """Search for parcels."""
    async def run_search():
        print_banner()

        config = get_config()
        engine = TerraJinkiEngine(config)

        logger.info(f"Searching: {args.query}")

        result = await engine.natural_language_search(args.query)

        print("\n" + "=" * 60)
        print("SEARCH RESULTS")
        print("=" * 60)

        print(f"\nQuery: {args.query}")
        print(f"Interpreted as: {result.interpreted_query}")
        print(f"Total matches: {result.total_matches}")
        print(f"Search time: {result.search_duration_ms:.1f}ms")

        if result.parcels:
            print(f"\nTop Results:")
            for i, parcel in enumerate(result.parcels[:10], 1):
                print(f"  {i}. {parcel.county}, {parcel.state} - {parcel.acreage:.1f} acres")

        print("=" * 60)

    asyncio.run(run_search())


def cmd_demo(args):
    """Run interactive demo."""
    async def run_demo():
        print_banner()

        config = get_config()
        engine = TerraJinkiEngine(config)

        print("\n" + "=" * 60)
        print("TERRAJINKI DEMO")
        print("=" * 60)

        # Create sample parcels
        sample_parcels = [
            Parcel(
                state="TX",
                county="Harris",
                municipality="Houston",
                acreage=75,
                zoning_type=ZoningType.AGRICULTURAL,
                solar_permission=SolarPermission.BY_RIGHT,
                centroid=GeoPoint(29.7604, -95.3698),
                nearest_substation_mi=2.5,
            ),
            Parcel(
                state="CA",
                county="Kern",
                municipality="Bakersfield",
                acreage=120,
                zoning_type=ZoningType.AGRICULTURAL,
                solar_permission=SolarPermission.CONDITIONAL_USE,
                centroid=GeoPoint(35.3733, -119.0187),
                nearest_substation_mi=4.0,
            ),
            Parcel(
                state="NC",
                county="Wake",
                municipality="Raleigh",
                acreage=45,
                zoning_type=ZoningType.AGRICULTURAL,
                solar_permission=SolarPermission.UNKNOWN,
                centroid=GeoPoint(35.7796, -78.6382),
                nearest_substation_mi=6.0,
            ),
        ]

        print("\nCreating sample parcels...")
        for parcel in sample_parcels:
            p = await engine.create_parcel(parcel)
            print(f"  Created: {p.county}, {p.state} ({p.acreage} acres)")

        # Quick score all parcels
        print("\nRunning quick scores...")
        scores = await engine.batch_score_parcels(sample_parcels)

        for parcel, score in zip(sample_parcels, scores):
            qs = score.get("quick_score", 0)
            rec = score.get("recommendation", "unknown")
            print(f"  {parcel.county}, {parcel.state}: {qs:.0f}/100 - {rec}")

        # Full analysis on best parcel
        best_idx = max(range(len(scores)), key=lambda i: scores[i].get("quick_score", 0))
        best_parcel = sample_parcels[best_idx]

        print(f"\nRunning full analysis on best parcel: {best_parcel.county}, {best_parcel.state}...")

        analysis = await engine.analyze_site(best_parcel)

        if analysis.score:
            print(f"\n  Overall Score: {analysis.score.overall_score:.1f}/100")
            print(f"  Viability: {analysis.score.viability}")
            print(f"  Recommendation: {analysis.proceed_recommendation}")

        print("\n" + "=" * 60)
        print("Demo complete! Try running 'terrajinki serve' to start the API.")
        print("=" * 60)

    asyncio.run(run_demo())


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TerraJinki - AI-Powered Renewable Energy Site Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a site")
    analyze_parser.add_argument("--state", required=True, help="State abbreviation")
    analyze_parser.add_argument("--county", required=True, help="County name")
    analyze_parser.add_argument("--acreage", type=float, required=True, help="Parcel acreage")
    analyze_parser.add_argument("--latitude", type=float, help="Latitude")
    analyze_parser.add_argument("--longitude", type=float, help="Longitude")
    analyze_parser.add_argument("--substation-distance", type=float, default=5.0, help="Distance to substation (miles)")
    analyze_parser.add_argument("--project-type", default="utility_solar", help="Project type")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search parcels")
    search_parser.add_argument("query", help="Natural language search query")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run interactive demo")

    args = parser.parse_args()

    if args.command == "serve":
        cmd_serve(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "demo":
        cmd_demo(args)
    else:
        print_banner()
        parser.print_help()


if __name__ == "__main__":
    main()
