"""
Paces - AI-Powered Renewable Energy Site Development Platform

Usage:
    python -m paces.main                    # Start API server
    python -m paces.main api --port 8000    # Start API with custom port
    python -m paces.main analyze --parcel <id>  # Analyze a parcel
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from loguru import logger

from paces import __version__
from paces.core.config import load_config


def setup_logging(level: str = "INFO") -> None:
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        colorize=True,
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Paces - AI-Powered Renewable Energy Site Development Platform",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Paces v{__version__}",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # API command
    api_parser = subparsers.add_parser("api", help="Start API server")
    api_parser.add_argument("--host", default="0.0.0.0")
    api_parser.add_argument("--port", type=int, default=8000)
    api_parser.add_argument("--reload", action="store_true")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a site")
    analyze_parser.add_argument("--parcel", required=True, help="Parcel ID or APN")
    analyze_parser.add_argument("--capacity", type=float, default=5.0)
    analyze_parser.add_argument("--output", default="./output")

    return parser.parse_args()


async def run_api(args: argparse.Namespace) -> None:
    """Run API server."""
    import uvicorn
    from paces.api.app import create_app

    config = load_config(args.config)
    app = create_app(config)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


async def run_analysis(args: argparse.Namespace) -> None:
    """Run site analysis."""
    from paces.core.engine import PacesEngine
    from paces.core.types import Parcel, GeoPoint, ZoningType

    config = load_config(args.config)
    engine = PacesEngine(config)

    if not await engine.initialize():
        logger.error("Engine initialization failed")
        return

    try:
        # Create a sample parcel for demo
        parcel = Parcel(
            apn=args.parcel,
            state="NC",
            county="Wake",
            municipality="Raleigh",
            acreage=50.0,
            zoning_type=ZoningType.AGRICULTURAL,
            centroid=GeoPoint(35.7796, -78.6382),
        )

        engine.add_parcel(parcel)

        logger.info(f"Analyzing parcel: {args.parcel}")
        report = await engine.analyze_site(
            parcel=parcel,
            target_capacity_mw=args.capacity,
        )

        if report:
            print("\n" + "=" * 60)
            print(report.executive_summary)
            print("=" * 60)

            # Generate report
            content = await engine.generate_report(report, format="markdown")
            print(content)
        else:
            logger.error("Analysis failed")

    finally:
        await engine.shutdown()


async def main() -> None:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.log_level)

    logger.info(f"Paces v{__version__}")
    logger.info("AI-Powered Renewable Energy Site Development Platform")
    logger.info("=" * 50)

    if args.command == "api":
        await run_api(args)
    elif args.command == "analyze":
        await run_analysis(args)
    else:
        # Default: start API
        args.host = "0.0.0.0"
        args.port = 8000
        args.reload = False
        await run_api(args)


def cli_main() -> None:
    """CLI entry point."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
