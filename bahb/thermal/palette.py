"""Thermal color palettes and visualization utilities."""

from __future__ import annotations

from enum import Enum

import cv2
import numpy as np
from numpy.typing import NDArray


class ThermalPalette(Enum):
    """Available thermal color palettes."""
    WHITE_HOT = "white_hot"
    BLACK_HOT = "black_hot"
    IRONBOW = "ironbow"
    RAINBOW = "rainbow"
    LAVA = "lava"
    ARCTIC = "arctic"
    INFERNO = "inferno"
    PLASMA = "plasma"
    VIRIDIS = "viridis"


# Custom palette lookup tables (256 colors each)
CUSTOM_PALETTES = {
    ThermalPalette.IRONBOW: None,  # Use built-in
    ThermalPalette.RAINBOW: None,  # Use built-in
}


def create_ironbow_lut() -> NDArray:
    """Create ironbow color palette LUT."""
    lut = np.zeros((256, 1, 3), dtype=np.uint8)

    for i in range(256):
        if i < 64:
            # Black to blue
            lut[i, 0] = [i * 4, 0, 0]
        elif i < 128:
            # Blue to red
            lut[i, 0] = [255, 0, (i - 64) * 4]
        elif i < 192:
            # Red to yellow
            lut[i, 0] = [255, (i - 128) * 4, 255 - (i - 128) * 4]
        else:
            # Yellow to white
            lut[i, 0] = [255, 255, (i - 192) * 4]

    return lut


def create_arctic_lut() -> NDArray:
    """Create arctic (cold) color palette LUT."""
    lut = np.zeros((256, 1, 3), dtype=np.uint8)

    for i in range(256):
        if i < 85:
            # Dark blue to light blue
            lut[i, 0] = [int(i * 3), int(50 + i * 1.5), int(100 + i * 1.5)]
        elif i < 170:
            # Light blue to cyan
            lut[i, 0] = [int(255), int(128 + (i - 85) * 1.5), int(255)]
        else:
            # Cyan to white
            val = int(255 - (255 - 200) * (i - 170) / 85)
            lut[i, 0] = [255, 255, val]

    return lut


def apply_palette(
    thermal_data: NDArray,
    palette: ThermalPalette = ThermalPalette.IRONBOW,
    temp_range: tuple[float, float] = None,
    invert: bool = False,
) -> NDArray:
    """
    Apply color palette to thermal data.

    Args:
        thermal_data: Temperature data (float) or normalized grayscale (uint8)
        palette: Color palette to apply
        temp_range: Optional temperature range for normalization
        invert: Invert the palette

    Returns:
        Colorized thermal image (BGR)
    """
    # Normalize to 0-255
    if thermal_data.dtype != np.uint8:
        if temp_range:
            temp_min, temp_max = temp_range
        else:
            temp_min, temp_max = thermal_data.min(), thermal_data.max()

        if temp_max - temp_min < 1e-6:
            normalized = np.zeros_like(thermal_data, dtype=np.uint8)
        else:
            normalized = ((thermal_data - temp_min) / (temp_max - temp_min) * 255).astype(np.uint8)
    else:
        normalized = thermal_data

    if invert:
        normalized = 255 - normalized

    # Apply colormap
    if palette == ThermalPalette.WHITE_HOT:
        # Simple grayscale (hot = white)
        colored = cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR)
    elif palette == ThermalPalette.BLACK_HOT:
        # Inverted grayscale (hot = black)
        colored = cv2.cvtColor(255 - normalized, cv2.COLOR_GRAY2BGR)
    elif palette == ThermalPalette.INFERNO:
        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_INFERNO)
    elif palette == ThermalPalette.PLASMA:
        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_PLASMA)
    elif palette == ThermalPalette.VIRIDIS:
        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_VIRIDIS)
    elif palette == ThermalPalette.RAINBOW:
        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
    elif palette == ThermalPalette.LAVA:
        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_HOT)
    elif palette == ThermalPalette.ARCTIC:
        lut = create_arctic_lut()
        colored = cv2.LUT(cv2.cvtColor(normalized, cv2.COLOR_GRAY2BGR), lut)
    else:  # IRONBOW and default
        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_INFERNO)

    return colored


def add_temperature_scale(
    image: NDArray,
    temp_range: tuple[float, float],
    palette: ThermalPalette = ThermalPalette.IRONBOW,
    position: str = "right",
    width: int = 40,
) -> NDArray:
    """
    Add a temperature scale bar to the image.

    Args:
        image: Input image
        temp_range: Temperature range (min, max)
        palette: Palette used for the image
        position: Scale position ("right", "left", "bottom")
        width: Width of the scale bar

    Returns:
        Image with scale bar
    """
    h, w = image.shape[:2]
    temp_min, temp_max = temp_range

    # Create scale bar
    if position in ("right", "left"):
        scale = np.linspace(255, 0, h).astype(np.uint8)
        scale = np.tile(scale.reshape(-1, 1), (1, width))
    else:  # bottom
        scale = np.linspace(0, 255, w).astype(np.uint8)
        scale = np.tile(scale.reshape(1, -1), (width, 1))

    # Apply same palette
    scale_colored = apply_palette(scale, palette)

    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    thickness = 1

    # Create output image
    if position == "right":
        output = np.zeros((h, w + width + 50, 3), dtype=np.uint8)
        output[:, :w] = image
        output[:, w:w+width] = scale_colored

        # Add temperature labels
        for i, temp in enumerate(np.linspace(temp_max, temp_min, 5)):
            y = int(h * i / 4)
            cv2.putText(output, f"{temp:.0f}C", (w + width + 5, y + 5),
                       font, font_scale, (255, 255, 255), thickness)

    elif position == "left":
        output = np.zeros((h, w + width + 50, 3), dtype=np.uint8)
        output[:, 50+width:] = image
        output[:, 50:50+width] = scale_colored

        for i, temp in enumerate(np.linspace(temp_max, temp_min, 5)):
            y = int(h * i / 4)
            cv2.putText(output, f"{temp:.0f}C", (5, y + 5),
                       font, font_scale, (255, 255, 255), thickness)

    else:  # bottom
        output = np.zeros((h + width + 30, w, 3), dtype=np.uint8)
        output[:h, :] = image
        output[h:h+width, :] = scale_colored

        for i, temp in enumerate(np.linspace(temp_min, temp_max, 5)):
            x = int(w * i / 4)
            cv2.putText(output, f"{temp:.0f}C", (x, h + width + 20),
                       font, font_scale, (255, 255, 255), thickness)

    return output


def create_isotherm_overlay(
    thermal_data: NDArray,
    threshold_temps: list[float],
    colors: list[tuple[int, int, int]] = None,
    alpha: float = 0.5,
) -> NDArray:
    """
    Create isotherm overlay showing temperature contours.

    Args:
        thermal_data: Temperature data
        threshold_temps: List of temperature thresholds
        colors: Colors for each threshold (BGR)
        alpha: Transparency of overlay

    Returns:
        Isotherm overlay image
    """
    h, w = thermal_data.shape[:2]
    overlay = np.zeros((h, w, 3), dtype=np.uint8)

    if colors is None:
        # Default: blue -> yellow -> red
        colors = [
            (255, 0, 0),    # Blue (cold)
            (0, 255, 255),  # Yellow
            (0, 0, 255),    # Red (hot)
        ]

    # Ensure we have enough colors
    while len(colors) < len(threshold_temps):
        colors.append((255, 255, 255))

    for i, temp in enumerate(sorted(threshold_temps)):
        mask = thermal_data >= temp
        contours, _ = cv2.findContours(
            mask.astype(np.uint8) * 255,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(overlay, contours, -1, colors[i], 2)

    return overlay


def highlight_anomalies(
    image: NDArray,
    thermal_data: NDArray,
    threshold: float,
    color: tuple[int, int, int] = (0, 0, 255),
    mode: str = "contour",
) -> NDArray:
    """
    Highlight thermal anomalies on an image.

    Args:
        image: Base image (RGB or thermal)
        thermal_data: Temperature data
        threshold: Temperature threshold for anomalies
        color: Highlight color (BGR)
        mode: "contour", "fill", or "marker"

    Returns:
        Image with highlighted anomalies
    """
    output = image.copy()

    # Find areas above threshold
    mask = thermal_data > threshold
    mask = mask.astype(np.uint8) * 255

    # Resize mask if needed
    if mask.shape[:2] != image.shape[:2]:
        mask = cv2.resize(mask, (image.shape[1], image.shape[0]))

    if mode == "contour":
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(output, contours, -1, color, 2)

    elif mode == "fill":
        colored_mask = np.zeros_like(output)
        colored_mask[mask > 0] = color
        output = cv2.addWeighted(output, 0.7, colored_mask, 0.3, 0)

    elif mode == "marker":
        # Find centroids of anomaly regions
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.circle(output, (cx, cy), 15, color, 2)
                cv2.drawMarker(output, (cx, cy), color, cv2.MARKER_CROSS, 20, 2)

    return output
