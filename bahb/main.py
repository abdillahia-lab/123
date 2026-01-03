"""
BAHB - Building And Hardware Baseline
Main entry point for the Drone Inspection System

Usage:
    python -m bahb.main --config configs/production.yaml
    python -m bahb.main --profile substation --site "Main Substation"
    python -m bahb.main --dev --visualize
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
from pathlib import Path

from loguru import logger

from bahb import __version__
from bahb.core.config import Config, load_config
from bahb.core.engine import InspectionEngine, run_inspection
from bahb.core.types import InspectionType


def setup_logging(level: str = "INFO", log_file: str = None) -> None:
    """Configure logging."""
    # Remove default handler
    logger.remove()

    # Console output
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File output
    if log_file:
        logger.add(
            log_file,
            level="DEBUG",
            rotation="100 MB",
            retention="7 days",
            compression="gz",
        )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="BAHB - Autonomous Drone Inspection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Start inspection with default config:
    python -m bahb.main

  Start substation inspection:
    python -m bahb.main --profile substation --site "Main Substation"

  Development mode with visualization:
    python -m bahb.main --dev --visualize

  Process single image:
    python -m bahb.main --image path/to/image.jpg --output results/
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"BAHB v{__version__}",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
    )

    parser.add_argument(
        "--profile",
        type=str,
        choices=["substation", "datacenter", "transmission", "solar", "wind"],
        default="substation",
        help="Inspection profile (default: substation)",
    )

    parser.add_argument(
        "--site",
        type=str,
        default="Unknown Site",
        help="Site name for the inspection",
    )

    parser.add_argument(
        "--pilot",
        type=str,
        default="",
        help="Pilot/Operator ID",
    )

    parser.add_argument(
        "--duration",
        type=int,
        help="Inspection duration in seconds (unlimited if not set)",
    )

    parser.add_argument(
        "--image",
        type=str,
        help="Process single image instead of live feed",
    )

    parser.add_argument(
        "--thermal",
        type=str,
        help="Thermal image to process with --image",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="./output",
        help="Output directory for results",
    )

    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip report generation",
    )

    parser.add_argument(
        "--dev",
        action="store_true",
        help="Development mode (additional logging)",
    )

    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Show visualization window",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path",
    )

    return parser.parse_args()


async def process_single_image(
    engine: InspectionEngine,
    image_path: str,
    thermal_path: str = None,
    output_dir: str = "./output",
) -> None:
    """Process a single image for inspection."""
    import cv2
    import json
    from datetime import datetime

    logger.info(f"Processing image: {image_path}")

    # Load image
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        return

    # Load thermal if provided
    thermal = None
    if thermal_path:
        thermal = cv2.imread(thermal_path)
        if thermal is None:
            logger.warning(f"Failed to load thermal image: {thermal_path}")

    # Process
    result = await engine.process_single_image(image, thermal)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save annotated image
    annotated = image.copy()
    for det in result.detections:
        bbox = det.bbox
        cv2.rectangle(
            annotated,
            (int(bbox.x1), int(bbox.y1)),
            (int(bbox.x2), int(bbox.y2)),
            (0, 255, 0),
            2,
        )
        cv2.putText(
            annotated,
            f"{det.class_name} {det.confidence:.0%}",
            (int(bbox.x1), int(bbox.y1) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

    # Mark anomalies
    for anomaly in result.anomalies:
        bbox = anomaly.detection.bbox
        color = {
            "CRITICAL": (0, 0, 255),
            "HIGH": (0, 128, 255),
            "MEDIUM": (0, 255, 255),
        }.get(anomaly.severity.name, (0, 255, 0))

        cv2.rectangle(
            annotated,
            (int(bbox.x1), int(bbox.y1)),
            (int(bbox.x2), int(bbox.y2)),
            color,
            3,
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_image = output_path / f"result_{timestamp}.jpg"
    cv2.imwrite(str(output_image), annotated)
    logger.info(f"Saved annotated image: {output_image}")

    # Save JSON results
    output_json = output_path / f"result_{timestamp}.json"
    with open(output_json, "w") as f:
        json.dump(result.to_dict(), f, indent=2, default=str)
    logger.info(f"Saved results: {output_json}")

    # Print summary
    print("\n" + "=" * 60)
    print("INSPECTION RESULTS")
    print("=" * 60)
    print(f"Detections: {len(result.detections)}")
    print(f"Anomalies:  {len(result.anomalies)}")

    if result.anomalies:
        print("\nAnomalies Found:")
        for a in result.anomalies:
            print(f"  [{a.severity.name}] {a.type}: {a.description}")

    if result.vlm_description:
        print("\nAI Analysis:")
        print(f"  {result.vlm_description}")

    print("=" * 60 + "\n")


async def run_live_inspection(args: argparse.Namespace) -> None:
    """Run live inspection from camera feed."""
    config = load_config(args.config)
    engine = InspectionEngine(config)

    # Setup signal handlers
    shutdown_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown signal received")
        shutdown_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        # Initialize
        if not await engine.initialize():
            logger.error("Engine initialization failed")
            return

        # Map profile to inspection type
        type_map = {
            "substation": InspectionType.SUBSTATION,
            "datacenter": InspectionType.DATACENTER,
            "transmission": InspectionType.TRANSMISSION_LINE,
            "solar": InspectionType.SOLAR_FARM,
            "wind": InspectionType.WIND_TURBINE,
        }
        inspection_type = type_map.get(args.profile, InspectionType.SUBSTATION)

        # Start inspection
        session_id = await engine.start_inspection(
            inspection_type=inspection_type,
            site_name=args.site,
            pilot_id=args.pilot,
        )

        logger.info(f"Inspection started: {session_id}")
        logger.info(f"Profile: {args.profile}, Site: {args.site}")

        # Visualization window
        if args.visualize:
            import cv2
            cv2.namedWindow("BAHB Inspection", cv2.WINDOW_NORMAL)

        # Main loop
        start_time = asyncio.get_event_loop().time()

        while not shutdown_event.is_set():
            # Check duration
            if args.duration:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed >= args.duration:
                    logger.info("Duration limit reached")
                    break

            # Get metrics
            metrics = engine.get_metrics()

            # Log periodic status
            if metrics["frame_count"] % 100 == 0:
                logger.info(
                    f"Frames: {metrics['frame_count']} | "
                    f"Anomalies: {sum(metrics['anomaly_counts'].values())} | "
                    f"FPS: {metrics['pipeline']['fps']:.1f}"
                )

            await asyncio.sleep(0.1)

        # Stop and generate report
        report_path = await engine.stop_inspection(
            generate_report=not args.no_report
        )

        if report_path:
            logger.info(f"Report generated: {report_path}")

    finally:
        await engine.shutdown()
        if args.visualize:
            cv2.destroyAllWindows()


async def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Setup logging
    log_level = "DEBUG" if args.dev else args.log_level
    setup_logging(level=log_level, log_file=args.log_file)

    logger.info(f"BAHB Drone Inspection System v{__version__}")
    logger.info("=" * 50)

    # Single image mode
    if args.image:
        config = load_config(args.config)
        engine = InspectionEngine(config)

        if not await engine.initialize():
            logger.error("Engine initialization failed")
            return

        await process_single_image(
            engine,
            args.image,
            args.thermal,
            args.output,
        )
        await engine.shutdown()

    # Live inspection mode
    else:
        await run_live_inspection(args)


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
