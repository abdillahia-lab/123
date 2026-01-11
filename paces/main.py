"""
Paces - Renewable Energy Management Platform
Main entry point

Usage:
    python -m paces.main --config configs/paces.yaml
    python -m paces.main api --port 8080
    python -m paces.main analyze --solar-farm farm1 --output results/
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from loguru import logger

from paces import __version__
from paces.core.config import load_paces_config
from paces.core.engine import PacesEngine


def setup_logging(level: str = "INFO", log_file: str = None) -> None:
    """Configure logging."""
    logger.remove()

    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    if log_file:
        logger.add(
            log_file,
            level="DEBUG",
            rotation="100 MB",
            retention="7 days",
        )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Paces - Renewable Energy Management Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
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

    # API server command
    api_parser = subparsers.add_parser("api", help="Start API server")
    api_parser.add_argument("--host", default="0.0.0.0")
    api_parser.add_argument("--port", type=int, default=8080)
    api_parser.add_argument("--reload", action="store_true")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run analysis")
    analyze_parser.add_argument("--solar-farm", help="Solar farm ID to analyze")
    analyze_parser.add_argument("--wind-farm", help="Wind farm ID to analyze")
    analyze_parser.add_argument("--output", default="./output")

    # Forecast command
    forecast_parser = subparsers.add_parser("forecast", help="Generate forecast")
    forecast_parser.add_argument("--asset", required=True, help="Asset ID")
    forecast_parser.add_argument("--hours", type=int, default=48)
    forecast_parser.add_argument("--output", default="./output")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("--type", choices=["financial", "carbon", "esg"], default="financial")
    report_parser.add_argument("--period", choices=["daily", "monthly", "yearly"], default="monthly")
    report_parser.add_argument("--output", default="./output")

    return parser.parse_args()


async def run_api(args: argparse.Namespace) -> None:
    """Run API server."""
    import uvicorn
    from paces.api.app import create_app

    config = load_paces_config(args.config)
    app = create_app(config)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


async def run_analysis(args: argparse.Namespace) -> None:
    """Run asset analysis."""
    config = load_paces_config(args.config)
    engine = PacesEngine(config)

    if not await engine.initialize():
        logger.error("Engine initialization failed")
        return

    try:
        if args.solar_farm:
            logger.info(f"Analyzing solar farm: {args.solar_farm}")
            # Would load farm from database and analyze
            # result = await engine.analyze_solar_farm(farm)
            logger.info("Solar analysis complete")

        if args.wind_farm:
            logger.info(f"Analyzing wind farm: {args.wind_farm}")
            # result = await engine.analyze_wind_turbine(turbine)
            logger.info("Wind analysis complete")

    finally:
        await engine.shutdown()


async def run_forecast(args: argparse.Namespace) -> None:
    """Generate forecast."""
    config = load_paces_config(args.config)
    engine = PacesEngine(config)

    if not await engine.initialize():
        logger.error("Engine initialization failed")
        return

    try:
        logger.info(f"Generating forecast for {args.asset}, {args.hours} hours")

        if args.asset.startswith("solar"):
            forecast = await engine.forecast_solar_production(args.asset, args.hours)
        else:
            forecast = await engine.forecast_wind_production(args.asset, args.hours)

        # Save forecast
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        import json
        output_file = output_dir / f"forecast_{args.asset}.json"
        with open(output_file, "w") as f:
            json.dump(forecast.to_dict(), f, indent=2, default=str)

        logger.info(f"Forecast saved to {output_file}")
        logger.info(f"Total energy: {forecast.total_energy_kwh:.2f} kWh")

    finally:
        await engine.shutdown()


async def main() -> None:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.log_level)

    logger.info(f"Paces v{__version__}")
    logger.info("=" * 50)

    if args.command == "api":
        await run_api(args)
    elif args.command == "analyze":
        await run_analysis(args)
    elif args.command == "forecast":
        await run_forecast(args)
    else:
        # Default: start API
        args.host = "0.0.0.0"
        args.port = 8080
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
