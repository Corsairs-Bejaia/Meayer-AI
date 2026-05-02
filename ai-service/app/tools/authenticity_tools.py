import asyncio
import io
import logging
import numpy as np
import cv2
from PIL import Image
from app.agents.base import BaseTool, ToolResult, AgentContext

logger = logging.getLogger(__name__)


class ELATool(BaseTool):
    """
    Error Level Analysis — detects JPEG compression inconsistencies
    caused by image splicing/editing.
    """

    @property
    def name(self) -> str:
        return "ela_analysis"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        if not image_bytes:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._analyze, image_bytes)
        return result

    def _analyze(self, image_bytes: bytes) -> ToolResult:
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            # Re-save at 90% quality and compute difference
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            buf.seek(0)
            resaved = Image.open(buf).convert("RGB")

            ela_arr = np.abs(np.array(img, dtype=np.float32) - np.array(resaved, dtype=np.float32))
            ela_arr = (ela_arr * 10).clip(0, 255).astype(np.uint8)  # Amplify differences

            # Analyze anomalous regions
            gray_ela = cv2.cvtColor(ela_arr, cv2.COLOR_RGB2GRAY)
            mean_ela = float(gray_ela.mean())
            max_ela = float(gray_ela.max())

            # High ELA values indicate potential tampering
            # Threshold: mean > 15 or max > 100 suggests editing
            tampering_detected = mean_ela > 15 or max_ela > 100
            suspicious_area_pct = float((gray_ela > 50).sum() / gray_ela.size * 100)

            # Invert: high ELA = lower authenticity confidence
            # Score = 1.0 if clean, 0.0 if heavily tampered
            confidence = max(0.0, min(1.0, 1.0 - (mean_ela / 30.0)))

            return ToolResult(
                tool_name=self.name,
                output={
                    "tampering_detected": tampering_detected,
                    "tampering_severity": "high" if mean_ela > 20 else "medium" if mean_ela > 10 else "low",
                    "mean_ela_value": round(mean_ela, 2),
                    "max_ela_value": round(max_ela, 2),
                    "suspicious_region_pct": round(suspicious_area_pct, 2),
                },
                confidence=confidence,
                processing_time_ms=0.0,
            )
        except Exception as e:
            logger.error(f"ELA error: {e}")
            return ToolResult(tool_name=self.name, output=None, confidence=0.5,
                              processing_time_ms=0.0, error=str(e))


class StampDetectorTool(BaseTool):
    """
    Detects official stamps (circular/rectangular, blue/red) using
    Hough circles and HSV color filtering.
    """

    @property
    def name(self) -> str:
        return "stamp_detector"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        if not image_bytes:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._detect, image_bytes)

    def _detect(self, image_bytes: bytes) -> ToolResult:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Blue ink range
            blue_mask = cv2.inRange(hsv, np.array([100, 80, 80]), np.array([130, 255, 255]))
            # Red ink range (two ranges for hue wrap-around)
            red_mask1 = cv2.inRange(hsv, np.array([0, 80, 80]), np.array([10, 255, 255]))
            red_mask2 = cv2.inRange(hsv, np.array([170, 80, 80]), np.array([180, 255, 255]))
            color_mask = blue_mask | red_mask1 | red_mask2

            color_pixel_pct = float(color_mask.sum() / 255) / color_mask.size

            # Detect circles (round stamps)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (9, 9), 2)
            circles = cv2.HoughCircles(
                blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
                param1=50, param2=30, minRadius=20, maxRadius=150
            )

            circle_count = len(circles[0]) if circles is not None else 0
            stamp_detected = circle_count > 0 or color_pixel_pct > 0.005

            confidence = 0.9 if stamp_detected else 0.5

            return ToolResult(
                tool_name=self.name,
                output={
                    "detected": stamp_detected,
                    "count": circle_count,
                    "color_match": color_pixel_pct > 0.005,
                    "color_coverage_pct": round(color_pixel_pct * 100, 3),
                },
                confidence=confidence,
                processing_time_ms=0.0,
            )
        except Exception as e:
            logger.error(f"StampDetector error: {e}")
            return ToolResult(tool_name=self.name, output={"detected": False},
                              confidence=0.5, processing_time_ms=0.0, error=str(e))


class SignatureDetectorTool(BaseTool):
    """
    Detects handwritten signatures in the bottom third of the document
    using contour complexity analysis.
    """

    @property
    def name(self) -> str:
        return "signature_detector"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        if not image_bytes:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._detect, image_bytes)

    def _detect(self, image_bytes: bytes) -> ToolResult:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            h, w = img.shape[:2]

            # Focus on bottom third
            roi = img[int(h * 0.65):h, 0:w]
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Signature = complex irregular strokes
            # Filter by area (not too small/large) and irregularity
            sig_contours = [
                c for c in contours
                if 200 < cv2.contourArea(c) < 50000
                and cv2.arcLength(c, True) > 100
            ]

            complexity = sum(len(c) for c in sig_contours)
            detected = len(sig_contours) > 0 and complexity > 50
            confidence = min(0.9, complexity / 500.0) if detected else 0.4

            return ToolResult(
                tool_name=self.name,
                output={
                    "detected": detected,
                    "complexity": complexity,
                    "contour_count": len(sig_contours),
                },
                confidence=confidence,
                processing_time_ms=0.0,
            )
        except Exception as e:
            logger.error(f"SignatureDetector error: {e}")
            return ToolResult(tool_name=self.name, output={"detected": False},
                              confidence=0.5, processing_time_ms=0.0, error=str(e))


class PhotocopyDetectorTool(BaseTool):
    """
    Detects if the document is a photocopy based on histogram analysis,
    sharpness, and color depth.
    """

    @property
    def name(self) -> str:
        return "photocopy_detector"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        if not image_bytes:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._detect, image_bytes)

    def _detect(self, image_bytes: bytes) -> ToolResult:
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 1. Sharpness (Laplacian variance — photocopies are blurry)
            laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

            # 2. Histogram bimodality (photocopy = concentrated near 0/255)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
            dark_pct = float(hist[:50].sum() / hist.sum())
            bright_pct = float(hist[200:].sum() / hist.sum())
            bimodal = dark_pct + bright_pct > 0.7

            # 3. Color saturation — photocopy has low saturation
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            mean_saturation = float(hsv[:, :, 1].mean())

            is_photocopy = (laplacian_var < 50) or (bimodal and mean_saturation < 20)
            confidence = 0.85 if is_photocopy else 0.8

            return ToolResult(
                tool_name=self.name,
                output={
                    "is_photocopy": is_photocopy,
                    "sharpness": round(laplacian_var, 2),
                    "mean_saturation": round(mean_saturation, 2),
                    "bimodal_histogram": bimodal,
                },
                confidence=confidence,
                processing_time_ms=0.0,
            )
        except Exception as e:
            logger.error(f"PhotocopyDetector error: {e}")
            return ToolResult(tool_name=self.name, output={"is_photocopy": False},
                              confidence=0.5, processing_time_ms=0.0, error=str(e))


class MetadataAnalyzerTool(BaseTool):
    """
    Analyzes EXIF metadata for signs of digital editing.
    """

    @property
    def name(self) -> str:
        return "metadata_analyzer"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        if not image_bytes:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes")

        try:
            from PIL.ExifTags import TAGS
            img = Image.open(io.BytesIO(image_bytes))
            exif_data = img._getexif() or {}

            exif = {TAGS.get(k, k): v for k, v in exif_data.items()}

            software = str(exif.get("Software", ""))
            editing_software = ["photoshop", "gimp", "lightroom", "paint", "pixelmator"]
            editing_detected = any(s in software.lower() for s in editing_software)

            date_original = exif.get("DateTimeOriginal")
            date_modified = exif.get("DateTime")
            date_mismatch = bool(date_original and date_modified and date_original != date_modified)

            confidence = 0.5 if editing_detected else 0.85

            return ToolResult(
                tool_name=self.name,
                output={
                    "editing_detected": editing_detected,
                    "software": software,
                    "date_mismatch": date_mismatch,
                    "date_original": str(date_original) if date_original else None,
                    "date_modified": str(date_modified) if date_modified else None,
                },
                confidence=confidence,
                processing_time_ms=0.0,
            )
        except Exception as e:
            logger.error(f"MetadataAnalyzer error: {e}")
            return ToolResult(tool_name=self.name,
                              output={"editing_detected": False, "software": ""},
                              confidence=0.7, processing_time_ms=0.0, error=str(e))
