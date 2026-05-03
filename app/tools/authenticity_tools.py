import cv2
import numpy as np
import logging
from app.agents.base import BaseTool, ToolResult, AgentContext
from app.tools.gemini_tool import GeminiVisionTool

logger = logging.getLogger(__name__)

class ELATool(BaseTool):
    @property
    def name(self) -> str:
        return "ela_analysis"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        if not image_bytes:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes")
        
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            quality = 90
            _, encoded_img = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            resaved_img = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)
            
            diff = cv2.absdiff(img, resaved_img)
            mean_ela = float(np.mean(diff))
            max_ela = float(np.max(diff))
            
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(diff_gray, 15, 255, cv2.THRESH_BINARY)
            suspicious_area_pct = float(np.sum(thresh == 255) / thresh.size)
            
            tampering_detected = bool(mean_ela > 5.0 or suspicious_area_pct > 0.05)
            confidence = 1.0 - (min(mean_ela, 20) / 20.0)
            
            return ToolResult(
                tool_name=self.name,
                output={
                    "tampering_detected": tampering_detected,
                    "ela_level": "high" if mean_ela > 20 else "medium" if mean_ela > 10 else "low",
                    "mean_error": round(mean_ela, 2),
                    "max_error": round(max_ela, 2),
                    "suspicious_area_pct": round(suspicious_area_pct, 2),
                },
                confidence=float(confidence),
                processing_time_ms=0.0,
            )
        except Exception as e:
            logger.error(f"ELA tool error: {e}")
            return ToolResult(tool_name=self.name, output=None, confidence=0.5,
                              processing_time_ms=0.0, error=str(e))

class StampDetectorTool(BaseTool):
    @property
    def name(self) -> str:
        return "stamp_detector"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.medianBlur(gray, 5)
            circles = cv2.HoughCircles(
                blurred, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
                param1=50, param2=30, minRadius=20, maxRadius=100
            )
            
            stamp_detected = circles is not None
            circle_count = int(len(circles[0])) if circles is not None else 0
            
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lower_blue = np.array([100, 50, 50])
            upper_blue = np.array([130, 255, 255])
            mask = cv2.inRange(hsv, lower_blue, upper_blue)
            color_pixel_pct = float(np.sum(mask > 0) / mask.size)
            
            is_colored = bool(color_pixel_pct > 0.005)
            
            return ToolResult(
                tool_name=self.name,
                output={
                    "stamp_detected": bool(stamp_detected or is_colored),
                    "circle_count": circle_count,
                    "is_colored_stamp": is_colored,
                    "color_density": round(color_pixel_pct * 100, 3),
                },
                confidence=0.9 if stamp_detected else 0.5,
                processing_time_ms=0.0,
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0, processing_time_ms=0.0, error=str(e))

class SignatureDetectorTool(BaseTool):
    @property
    def name(self) -> str:
        return "signature_detector"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            sig_contours = [c for c in contours if cv2.contourArea(c) > 500 and cv2.contourArea(c) < 5000]
            
            detected = bool(len(sig_contours) > 0)
            complexity = float(sum(len(c) for c in sig_contours) / max(len(sig_contours), 1))
            
            return ToolResult(
                tool_name=self.name,
                output={
                    "signature_detected": detected,
                    "complexity_score": round(complexity, 2),
                    "candidate_regions": int(len(sig_contours)),
                },
                confidence=0.8 if detected else 0.4,
                processing_time_ms=0.0,
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0, processing_time_ms=0.0, error=str(e))

class PhotocopyDetectorTool(BaseTool):
    @property
    def name(self) -> str:
        return "photocopy_detector"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            saturation = hsv[:,:,1]
            mean_saturation = float(np.mean(saturation))
            
            laplacian_var = float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
            
            hist = cv2.calcHist([cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)], [0], None, [256], [0, 256])
            bimodal_pct = float((np.sum(hist[0:20]) + np.sum(hist[235:255])) / img.size)
            bimodal = bool(bimodal_pct > 0.8)
            
            is_photocopy = bool(mean_saturation < 15 and bimodal)
            
            return ToolResult(
                tool_name=self.name,
                output={
                    "is_photocopy": is_photocopy,
                    "sharpness_score": round(laplacian_var, 2),
                    "color_saturation": round(mean_saturation, 2),
                    "is_bimodal": bimodal,
                },
                confidence=0.85 if is_photocopy else 0.7,
                processing_time_ms=0.0,
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0, processing_time_ms=0.0, error=str(e))

class MetadataAnalyzerTool(BaseTool):
    @property
    def name(self) -> str:
        return "metadata_analyzer"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            import io
            
            img = Image.open(io.BytesIO(image_bytes))
            info = img.getexif()
            
            exif = {}
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                exif[decoded] = value
                
            software = str(exif.get("Software", "None"))
            editing_detected = bool(any(s in software.lower() for s in ["photoshop", "gimp", "canva", "adobe"]))
            
            date_original = exif.get("DateTimeOriginal")
            date_modified = exif.get("DateTime")
            date_mismatch = bool(date_original and date_modified and date_original != date_modified)
            
            confidence = 0.9 if editing_detected else 0.6
            
            return ToolResult(
                tool_name=self.name,
                output={
                    "editing_software_detected": editing_detected,
                    "software_name": software,
                    "date_tampering_detected": date_mismatch,
                    "original_date": str(date_original) if date_original else None,
                    "modification_date": str(date_modified) if date_modified else None,
                },
                confidence=confidence,
                processing_time_ms=0.0,
            )
        except Exception as e:
            logger.error(f"MetadataAnalyzer error: {e}")
            return ToolResult(tool_name=self.name, output=None, confidence=0.5,
                              processing_time_ms=0.0, error=str(e))


class AIGenerationDetectorTool(GeminiVisionTool):
    @property
    def name(self) -> str:
        return "ai_generation_detector"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        prompt = (
            "Analyze this document for signs of AI generation (DALL-E, Midjourney, etc.). "
            "Specific Red Flags: "
            "1. 'Too perfect' or artistic backgrounds/shadows (typical of DALL-E). "
            "2. Hallucinated logos or distorted Algerian administrative seals. "
            "3. Font inconsistencies within the same paragraph. "
            "4. Meaningless or distorted Arabic/French text strings. "
            "Return JSON: {\"is_ai_generated\": true/false, \"confidence\": 0.0-1.0, \"reasoning\": \"...\"}"
        )
        kwargs["prompt"] = prompt
        result = await super().execute(context, **kwargs)
        
        if result.output and "text" in result.output:
            try:
                import json
                import re
                clean_json = re.sub(r"```json\n|\n```", "", result.output["text"]).strip()
                data = json.loads(clean_json)
                return ToolResult(
                    tool_name=self.name,
                    output={
                        "is_ai_generated": bool(data.get("is_ai_generated", False)),
                        "ai_score": float(data.get("confidence", 0)),
                        "reasoning": str(data.get("reasoning", ""))
                    },
                    confidence=float(data.get("confidence", 0.5)),
                    processing_time_ms=0.0
                )
            except Exception as e:
                logger.error(f"Failed to parse AI detection JSON: {e}")
        
        return result
