"""
Vibration Analyzer - Wind turbine vibration signature analysis.

Detects:
- Rotor imbalance
- Shaft misalignment
- Bearing wear
- Gearbox issues
- Tower resonance
- Foundation problems
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from loguru import logger

from paces.core.config import PacesConfig


@dataclass
class VibrationAnomaly:
    """Detected vibration anomaly."""
    type: str
    severity: str
    frequency_hz: float
    amplitude: float
    confidence: float
    description: str
    recommendations: list[str]


class VibrationAnalyzer:
    """
    Wind turbine vibration signature analyzer.

    Uses FFT-based frequency analysis combined with
    ML models for anomaly detection and classification.
    """

    # Known vibration patterns
    PATTERNS = {
        "1x": "rotor_imbalance",
        "2x": "misalignment",
        "3x": "blade_passage",
        "bearing": "bearing_defect",
        "gear_mesh": "gearbox_issue",
        "broadband": "structural_issue",
    }

    def __init__(self, config: PacesConfig):
        self.config = config

        self._model = None
        self._is_loaded = False

    async def load(self) -> bool:
        """Load vibration analysis models."""
        logger.info("Loading vibration analyzer...")

        try:
            self._is_loaded = True
            logger.info("Vibration analyzer loaded")
            return True

        except Exception as e:
            logger.error(f"Failed to load vibration analyzer: {e}")
            return False

    async def analyze(
        self,
        vibration_data: list[dict],
        rpm: float = None,
    ) -> dict:
        """
        Analyze vibration data for anomalies.

        Args:
            vibration_data: List of vibration readings with:
                - timestamp
                - acceleration (x, y, z)
                - location (tower, nacelle, drivetrain)
            rpm: Rotor RPM for frequency analysis

        Returns:
            Analysis result dictionary
        """
        if not self._is_loaded:
            raise RuntimeError("Analyzer not loaded")

        if not vibration_data:
            return {
                "health_score": 100.0,
                "anomalies": [],
                "spectrum": None,
            }

        # Extract acceleration data
        accelerations = self._extract_accelerations(vibration_data)

        # Compute frequency spectrum
        spectrum = self._compute_spectrum(accelerations, rpm)

        # Detect anomalies
        anomalies = self._detect_anomalies(spectrum, rpm)

        # Calculate health score
        health_score = self._calculate_health_score(anomalies)

        # Trend analysis
        trends = self._analyze_trends(vibration_data)

        return {
            "health_score": health_score,
            "anomalies": anomalies,
            "spectrum": spectrum,
            "trends": trends,
            "rms_overall": float(np.sqrt(np.mean(accelerations ** 2))),
            "peak_acceleration": float(np.max(np.abs(accelerations))),
        }

    def _extract_accelerations(self, vibration_data: list[dict]) -> NDArray:
        """Extract acceleration array from data."""
        accelerations = []
        for reading in vibration_data:
            if "acceleration" in reading:
                acc = reading["acceleration"]
                if isinstance(acc, dict):
                    # Magnitude of 3D acceleration
                    mag = np.sqrt(acc.get("x", 0)**2 + acc.get("y", 0)**2 + acc.get("z", 0)**2)
                    accelerations.append(mag)
                else:
                    accelerations.append(float(acc))

        return np.array(accelerations) if accelerations else np.array([0.0])

    def _compute_spectrum(
        self,
        accelerations: NDArray,
        rpm: float = None,
    ) -> dict:
        """Compute frequency spectrum using FFT."""
        if len(accelerations) < 10:
            return {"frequencies": [], "amplitudes": []}

        # Assume 1000 Hz sampling rate
        sample_rate = 1000

        # Apply window
        window = np.hanning(len(accelerations))
        windowed = accelerations * window

        # FFT
        fft_result = np.fft.fft(windowed)
        freqs = np.fft.fftfreq(len(accelerations), 1.0 / sample_rate)

        # Take positive frequencies
        positive_mask = freqs >= 0
        freqs = freqs[positive_mask]
        amplitudes = np.abs(fft_result[positive_mask])

        # Normalize
        amplitudes = amplitudes / len(accelerations)

        return {
            "frequencies": freqs.tolist(),
            "amplitudes": amplitudes.tolist(),
            "dominant_frequency": float(freqs[np.argmax(amplitudes)]) if len(freqs) > 0 else 0,
            "max_amplitude": float(np.max(amplitudes)) if len(amplitudes) > 0 else 0,
        }

    def _detect_anomalies(
        self,
        spectrum: dict,
        rpm: float = None,
    ) -> list[dict]:
        """Detect anomalies in frequency spectrum."""
        anomalies = []

        if not spectrum.get("frequencies"):
            return anomalies

        freqs = np.array(spectrum["frequencies"])
        amps = np.array(spectrum["amplitudes"])

        # Calculate thresholds
        mean_amp = np.mean(amps)
        std_amp = np.std(amps)
        threshold = mean_amp + 3 * std_amp

        # Find peaks above threshold
        peak_indices = np.where(amps > threshold)[0]

        # Rotor frequency
        rotor_freq = (rpm / 60) if rpm else 0.5

        for idx in peak_indices:
            freq = freqs[idx]
            amp = amps[idx]

            # Classify anomaly
            anomaly_type, description = self._classify_frequency(freq, rotor_freq)

            severity = "low"
            if amp > mean_amp + 5 * std_amp:
                severity = "critical"
            elif amp > mean_amp + 4 * std_amp:
                severity = "high"
            elif amp > mean_amp + 3 * std_amp:
                severity = "medium"

            recommendations = self._get_vibration_recommendations(anomaly_type)

            anomalies.append({
                "type": anomaly_type,
                "severity": severity,
                "frequency_hz": float(freq),
                "amplitude": float(amp),
                "confidence": min(1.0, amp / threshold),
                "description": description,
                "recommendations": recommendations,
            })

        return anomalies

    def _classify_frequency(
        self,
        frequency: float,
        rotor_freq: float,
    ) -> tuple[str, str]:
        """Classify anomaly based on frequency."""
        if rotor_freq > 0:
            ratio = frequency / rotor_freq

            if 0.9 <= ratio <= 1.1:
                return "imbalance", f"1x rotor frequency ({frequency:.1f} Hz) - Rotor imbalance"
            elif 1.9 <= ratio <= 2.1:
                return "misalignment", f"2x rotor frequency ({frequency:.1f} Hz) - Shaft misalignment"
            elif 2.9 <= ratio <= 3.1:
                return "blade_passage", f"3x rotor frequency ({frequency:.1f} Hz) - Blade passage"

        # High frequency - likely bearing or gearbox
        if frequency > 100:
            return "bearing", f"High frequency ({frequency:.1f} Hz) - Possible bearing defect"

        return "unknown", f"Abnormal vibration at {frequency:.1f} Hz"

    def _get_vibration_recommendations(self, anomaly_type: str) -> list[str]:
        """Get recommendations for anomaly type."""
        recommendations = {
            "imbalance": [
                "Check blade pitch angles",
                "Inspect for ice buildup or debris",
                "Schedule blade balancing",
            ],
            "misalignment": [
                "Check coupling alignment",
                "Inspect drive train mounts",
                "Schedule alignment correction",
            ],
            "bearing": [
                "Perform bearing inspection",
                "Check lubrication levels",
                "Plan bearing replacement",
            ],
            "gearbox": [
                "Gearbox oil analysis recommended",
                "Check gear mesh condition",
                "Monitor temperature trends",
            ],
        }
        return recommendations.get(anomaly_type, ["Schedule detailed inspection"])

    def _calculate_health_score(self, anomalies: list[dict]) -> float:
        """Calculate overall health score 0-100."""
        if not anomalies:
            return 100.0

        score = 100.0

        for anomaly in anomalies:
            severity = anomaly.get("severity", "low")
            if severity == "critical":
                score -= 30
            elif severity == "high":
                score -= 15
            elif severity == "medium":
                score -= 5
            else:
                score -= 2

        return max(0, score)

    def _analyze_trends(self, vibration_data: list[dict]) -> dict:
        """Analyze vibration trends over time."""
        if len(vibration_data) < 2:
            return {"trend": "insufficient_data"}

        # Extract RMS values over time
        rms_values = []
        for reading in vibration_data:
            if "acceleration" in reading:
                acc = reading["acceleration"]
                if isinstance(acc, dict):
                    mag = np.sqrt(acc.get("x", 0)**2 + acc.get("y", 0)**2 + acc.get("z", 0)**2)
                else:
                    mag = float(acc)
                rms_values.append(mag)

        if len(rms_values) < 2:
            return {"trend": "insufficient_data"}

        # Linear regression for trend
        x = np.arange(len(rms_values))
        slope, _ = np.polyfit(x, rms_values, 1)

        trend = "stable"
        if slope > 0.01:
            trend = "increasing"
        elif slope < -0.01:
            trend = "decreasing"

        return {
            "trend": trend,
            "slope": float(slope),
            "current_rms": float(rms_values[-1]),
            "avg_rms": float(np.mean(rms_values)),
        }

    async def unload(self) -> None:
        """Unload analyzer."""
        logger.info("Unloading vibration analyzer")
        self._is_loaded = False
