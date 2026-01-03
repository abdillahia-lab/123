"""Qwen2.5-VL-3B-AWQ Visual Language Model for inspection analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from numpy.typing import NDArray
from loguru import logger

from bahb.core.config import QwenVLConfig
from bahb.core.types import Detection, ThermalReading, Anomaly, SeverityLevel
from bahb.models.base import BaseModel


# Inspection prompts for different scenarios
INSPECTION_PROMPTS = {
    "general": """Analyze this infrastructure inspection image. Identify and describe:
1. Main equipment/components visible
2. Any visible damage, defects, or anomalies
3. Potential safety concerns
4. Maintenance recommendations

Be specific about locations and severity.""",

    "thermal": """Analyze this thermal image of infrastructure equipment. Focus on:
1. Hot spots - identify locations with abnormal temperatures
2. Temperature gradients that indicate issues
3. Comparison between similar components
4. Equipment health assessment based on thermal signature

Provide severity assessment: Normal, Warning, or Critical.""",

    "substation": """Analyze this substation inspection image. Examine:
1. Transformer condition (bushings, oil level, cooling)
2. Insulator integrity (cracks, contamination, flashover marks)
3. Conductor connections (hot joints, corrosion)
4. Vegetation clearance and encroachment
5. General structural condition

Rate each finding by severity and urgency.""",

    "datacenter": """Analyze this data center inspection image. Examine:
1. Server rack status and cable management
2. Cooling system operation (fans, vents, airflow)
3. Electrical connections and panels
4. Fire suppression system visibility
5. Floor condition and obstruction

Identify any issues that could affect operations.""",

    "defect": """Examine this image for defects. Specifically look for:
1. Cracks, fractures, or structural damage
2. Corrosion or material degradation
3. Contamination or foreign objects
4. Wear patterns indicating excessive use
5. Missing or damaged components

Describe each defect with location and recommended action.""",

    "comparison": """Compare the two images provided (before/after or thermal/visual).
1. Identify differences between the images
2. Assess changes in equipment condition
3. Highlight any degradation or improvement
4. Provide recommendations based on comparison

Be specific about locations and measurements where possible.""",
}


class QwenVLAnalyzer(BaseModel):
    """
    Qwen2.5-VL-3B-AWQ Visual Language Model for intelligent inspection analysis.

    Features:
    - Multi-image understanding
    - Detailed defect description
    - Contextual recommendations
    - AWQ quantization for edge deployment
    """

    def __init__(self, config: QwenVLConfig):
        super().__init__(
            model_path=config.model_path,
            device=config.device,
            half_precision=True,
        )
        self.config = config
        self.max_new_tokens = config.max_new_tokens
        self.temperature = config.temperature
        self.context_length = config.context_length

        self._model = None
        self._processor = None
        self._tokenizer = None

    def load(self) -> bool:
        """Load Qwen2.5-VL model."""
        try:
            return self._load_transformers()
        except Exception as e:
            logger.error(f"Failed to load Qwen2.5-VL: {e}")
            return False

    def _load_transformers(self) -> bool:
        """Load using transformers + AWQ."""
        try:
            import torch
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

            logger.info(f"Loading Qwen2.5-VL from: {self.model_path}")

            model_path = Path(self.model_path)

            # Check if local path exists, otherwise use HF model ID
            if not model_path.exists():
                model_id = "Qwen/Qwen2.5-VL-3B-Instruct-AWQ"
                logger.info(f"Local model not found, using: {model_id}")
            else:
                model_id = str(model_path)

            # Load processor
            self._processor = AutoProcessor.from_pretrained(
                model_id,
                trust_remote_code=True,
            )

            # Load model with AWQ quantization
            device = torch.device(self.device if torch.cuda.is_available() else "cpu")

            self._model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
                device_map="auto" if device.type == "cuda" else None,
                trust_remote_code=True,
            )

            if device.type != "cuda":
                self._model = self._model.to(device)

            self._model.eval()

            self._is_loaded = True
            logger.info("Qwen2.5-VL loaded successfully")
            return True

        except ImportError as e:
            logger.warning(f"Transformers import failed: {e}")
            return self._load_fallback()
        except Exception as e:
            logger.error(f"Failed to load Qwen2.5-VL: {e}")
            return self._load_fallback()

    def _load_fallback(self) -> bool:
        """Load fallback vision model."""
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            import torch

            logger.info("Loading BLIP as fallback")

            self._processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
            self._model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-large"
            )

            device = torch.device(self.device if torch.cuda.is_available() else "cpu")
            self._model = self._model.to(device)
            self._model.eval()

            self._use_blip_fallback = True
            self._is_loaded = True
            logger.info("BLIP fallback loaded")
            return True

        except Exception as e:
            logger.error(f"Fallback also failed: {e}")
            self._use_template_fallback = True
            self._is_loaded = True
            return True

    def unload(self) -> None:
        """Unload model resources."""
        self._model = None
        self._processor = None
        self._is_loaded = False

    def preprocess(self, image: NDArray) -> dict:
        """Preprocess image for Qwen2.5-VL."""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Resize if too large
        max_size = 1280
        h, w = rgb_image.shape[:2]
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_size = (int(w * scale), int(h * scale))
            rgb_image = cv2.resize(rgb_image, new_size)

        return {"image": rgb_image}

    def forward(self, inputs: dict) -> str:
        """This method is not used directly - use analyze methods instead."""
        return ""

    def postprocess(self, outputs: str, original_shape: tuple) -> str:
        """Return the analysis text directly."""
        return outputs

    def analyze(
        self,
        image: NDArray,
        prompt: Optional[str] = None,
        prompt_type: str = "general",
    ) -> str:
        """
        Analyze an inspection image with optional custom prompt.

        Args:
            image: Input image (BGR)
            prompt: Custom analysis prompt (overrides prompt_type)
            prompt_type: One of: general, thermal, substation, datacenter, defect

        Returns:
            Analysis text from the model
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded")

        if hasattr(self, "_use_template_fallback") and self._use_template_fallback:
            return self._template_analysis(image, prompt_type)

        # Get prompt
        if prompt is None:
            prompt = INSPECTION_PROMPTS.get(prompt_type, INSPECTION_PROMPTS["general"])

        # Preprocess
        processed = self.preprocess(image)
        rgb_image = processed["image"]

        if hasattr(self, "_use_blip_fallback") and self._use_blip_fallback:
            return self._analyze_blip(rgb_image, prompt)

        return self._analyze_qwen(rgb_image, prompt)

    def _analyze_qwen(self, rgb_image: NDArray, prompt: str) -> str:
        """Run Qwen2.5-VL analysis."""
        import torch
        from PIL import Image

        # Convert to PIL
        pil_image = Image.fromarray(rgb_image)

        # Prepare messages
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        # Process inputs
        text = self._processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self._processor(
            text=[text],
            images=[pil_image],
            return_tensors="pt",
            padding=True,
        )

        # Move to device
        device = next(self._model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Generate
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=self.temperature > 0,
            )

        # Decode
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        response = self._processor.decode(generated_ids, skip_special_tokens=True)

        return response.strip()

    def _analyze_blip(self, rgb_image: NDArray, prompt: str) -> str:
        """Run BLIP analysis (fallback)."""
        import torch
        from PIL import Image

        pil_image = Image.fromarray(rgb_image)

        # BLIP uses simpler prompting
        inputs = self._processor(
            pil_image,
            f"Question: {prompt} Answer:",
            return_tensors="pt",
        )

        device = next(self._model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=256,
            )

        response = self._processor.decode(outputs[0], skip_special_tokens=True)
        return response.strip()

    def _template_analysis(self, image: NDArray, prompt_type: str) -> str:
        """Template-based analysis when no model available."""
        # Basic image analysis using OpenCV
        analysis = []

        # Color analysis
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mean_brightness = np.mean(hsv[:, :, 2])

        if mean_brightness < 80:
            analysis.append("Image appears dark - may indicate low-light conditions or enclosed space.")
        elif mean_brightness > 200:
            analysis.append("Image appears bright - good visibility for inspection.")

        # Edge detection for structure analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size

        if edge_density > 0.15:
            analysis.append("High structural complexity detected - multiple components visible.")
        elif edge_density < 0.05:
            analysis.append("Low structural complexity - may be a uniform surface or distant view.")

        # Color temperature for thermal-like analysis
        b, g, r = cv2.split(image)
        if np.mean(r) > np.mean(b) * 1.3:
            analysis.append("Warm color tones detected - if thermal, indicates heat sources present.")

        analysis.append("\nNote: Full AI analysis requires model to be loaded.")
        analysis.append("Please verify findings with manual inspection.")

        return "\n".join(analysis)

    def analyze_with_detections(
        self,
        image: NDArray,
        detections: list[Detection],
        thermal_reading: Optional[ThermalReading] = None,
    ) -> str:
        """
        Analyze image with detection context for more accurate assessment.

        Args:
            image: Input image
            detections: List of detected objects
            thermal_reading: Optional thermal data

        Returns:
            Contextual analysis text
        """
        # Build context prompt
        context_parts = ["Analyze this inspection image with the following context:"]

        # Add detection info
        if detections:
            context_parts.append("\nDetected equipment:")
            for i, det in enumerate(detections, 1):
                context_parts.append(f"  {i}. {det.class_name} (confidence: {det.confidence:.1%})")

        # Add thermal info
        if thermal_reading:
            context_parts.append(f"\nThermal data:")
            context_parts.append(f"  - Temperature range: {thermal_reading.min_temp:.1f}°C to {thermal_reading.max_temp:.1f}°C")
            context_parts.append(f"  - Average: {thermal_reading.mean_temp:.1f}°C")
            context_parts.append(f"  - Hot spots detected: {len(thermal_reading.hotspot_locations)}")

        context_parts.append("\nProvide detailed analysis of equipment condition and any anomalies.")

        prompt = "\n".join(context_parts)
        return self.analyze(image, prompt=prompt)

    def generate_anomaly_description(
        self,
        image: NDArray,
        detection: Detection,
        thermal: Optional[ThermalReading] = None,
    ) -> tuple[str, list[str]]:
        """
        Generate detailed description and recommendations for an anomaly.

        Returns:
            Tuple of (description, recommendations)
        """
        # Crop to detection area with padding
        bbox = detection.bbox
        h, w = image.shape[:2]

        pad = 50
        x1 = int(max(0, bbox.x1 - pad))
        y1 = int(max(0, bbox.y1 - pad))
        x2 = int(min(w, bbox.x2 + pad))
        y2 = int(min(h, bbox.y2 + pad))

        crop = image[y1:y2, x1:x2]

        # Build specific prompt
        prompt = f"""Analyze this detected {detection.class_name} from an infrastructure inspection.

Detection confidence: {detection.confidence:.1%}
"""

        if thermal:
            prompt += f"""
Thermal data for this region:
- Max temperature: {thermal.max_temp:.1f}°C
- Temperature differential: {thermal.delta_t:.1f}°C
"""

        prompt += """
Provide:
1. A detailed description of the condition (2-3 sentences)
2. Severity assessment (Info/Low/Medium/High/Critical)
3. 2-3 specific maintenance recommendations

Format your response as:
DESCRIPTION: [description]
SEVERITY: [level]
RECOMMENDATIONS:
- [recommendation 1]
- [recommendation 2]
- [recommendation 3]
"""

        response = self.analyze(crop, prompt=prompt)

        # Parse response
        description = ""
        recommendations = []

        lines = response.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if line.startswith("DESCRIPTION:"):
                description = line.replace("DESCRIPTION:", "").strip()
                current_section = "description"
            elif line.startswith("SEVERITY:"):
                current_section = "severity"
            elif line.startswith("RECOMMENDATIONS:"):
                current_section = "recommendations"
            elif current_section == "description" and not line.startswith(("SEVERITY", "RECOMMENDATIONS")):
                description += " " + line
            elif current_section == "recommendations" and line.startswith("-"):
                recommendations.append(line[1:].strip())

        if not description:
            description = f"Detected {detection.class_name} requires inspection."
        if not recommendations:
            recommendations = ["Schedule routine inspection", "Document current condition"]

        return description.strip(), recommendations

    def compare_images(
        self,
        image1: NDArray,
        image2: NDArray,
        labels: tuple[str, str] = ("Before", "After"),
    ) -> str:
        """
        Compare two images for change detection.

        Args:
            image1: First image (e.g., baseline)
            image2: Second image (e.g., current)
            labels: Labels for the images

        Returns:
            Comparison analysis
        """
        # Create side-by-side comparison
        h1, w1 = image1.shape[:2]
        h2, w2 = image2.shape[:2]

        # Resize to same height
        target_h = min(h1, h2, 600)
        scale1 = target_h / h1
        scale2 = target_h / h2

        img1_resized = cv2.resize(image1, (int(w1 * scale1), target_h))
        img2_resized = cv2.resize(image2, (int(w2 * scale2), target_h))

        # Combine
        combined = np.hstack([img1_resized, img2_resized])

        prompt = f"""Compare these two infrastructure inspection images shown side by side.
Left image: {labels[0]}
Right image: {labels[1]}

""" + INSPECTION_PROMPTS["comparison"]

        return self.analyze(combined, prompt=prompt)

    def assess_severity(
        self,
        description: str,
        thermal_reading: Optional[ThermalReading] = None,
    ) -> SeverityLevel:
        """
        Assess severity level from description and thermal data.

        Args:
            description: Text description of finding
            thermal_reading: Optional thermal data

        Returns:
            SeverityLevel enum
        """
        description_lower = description.lower()

        # Critical indicators
        critical_keywords = ["critical", "immediate", "danger", "failure", "fire", "emergency", "unsafe"]
        if any(kw in description_lower for kw in critical_keywords):
            return SeverityLevel.CRITICAL

        # Thermal-based severity
        if thermal_reading:
            if thermal_reading.max_temp > 100 or thermal_reading.delta_t > 50:
                return SeverityLevel.CRITICAL
            elif thermal_reading.max_temp > 80 or thermal_reading.delta_t > 30:
                return SeverityLevel.HIGH
            elif thermal_reading.max_temp > 60 or thermal_reading.delta_t > 15:
                return SeverityLevel.MEDIUM

        # Text-based severity
        high_keywords = ["significant", "major", "severe", "urgent", "damage"]
        if any(kw in description_lower for kw in high_keywords):
            return SeverityLevel.HIGH

        medium_keywords = ["moderate", "attention", "monitor", "wear", "degradation"]
        if any(kw in description_lower for kw in medium_keywords):
            return SeverityLevel.MEDIUM

        low_keywords = ["minor", "slight", "cosmetic", "routine"]
        if any(kw in description_lower for kw in low_keywords):
            return SeverityLevel.LOW

        return SeverityLevel.INFO
