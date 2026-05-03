import logging
import re
from typing import Optional

from app.agents.base import BaseTool, ToolResult, AgentContext
from app.tools.gemini_tool import GeminiVisionTool

logger = logging.getLogger(__name__)

class GeminiClassifierTool(GeminiVisionTool):
    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        templates = kwargs.get("available_templates", [])
        slugs = []
        for t in templates:
            if isinstance(t, dict):
                slugs.append(t.get("slug"))
            else:
                slugs.append(getattr(t, "slug", "unknown"))
        
        template_list = ", ".join([f"'{s}'" for s in slugs if s])
        
        prompt = (
            f"Based on this image, identify the document type. Return ONLY the JSON slug from this list: {template_list}. "
        )
        kwargs["prompt"] = prompt
        result = await super().execute(context, **kwargs)
        
        if result.output and "text" in result.output:
            doc_type = result.output["text"].strip().strip("'").strip('"').lower()
            result.output["doc_type"] = doc_type
        
        return result


KEYWORD_PATTERNS = {
    "national_id": [
        r"biom[ée]trique", r"carte\s+d'identit", r"NATIONALE", r"REPUBLIQUE\s+ALGERIENNE",
        r"بطاقة\s+التعريف", r"الهوية\s+الوطنية",
    ],
    "diploma": [
        r"dipl[oô]me", r"mast[eè]re", r"bachelor", r"licence", r"doctorat",
        r"شهادة", r"دكتوراه", r"ليسانس",
    ],
    "affiliation_attestation": [
        r"attestation", r"affiliation", r"CNAS", r"caisse\s+nationale",
        r"شهادة\s+الانتساب", r"الصندوق\s+الوطني",
    ],
    "contract": [
        r"convention", r"contrat", r"accord", r"protocole",
        r"اتفاقية", r"عقد",
    ],
    "insurance_card": [
        r"chifa", r"assurance\s+maladie", r"carte\s+de\s+soin",
        r"شيفا", r"التأمين\s+الصحي",
    ],
    "ordonnance": [
        r"ordonnance", r"prescription", r"m[ée]dicament",
        r"وصفة\s+طبية",
    ],
    "birth_certificate": [
        r"acte\s+de\s+naissance", r"naissance", r"né\s+le",
        r"شهادة\s+الميلاد",
    ],
}


def _keyword_match(text: str) -> Optional[tuple[str, float]]:
    text_lower = text.lower()
    scores: dict[str, float] = {}
    for doc_type, patterns in KEYWORD_PATTERNS.items():
        matches = sum(1 for p in patterns if re.search(p, text_lower, re.IGNORECASE))
        if matches > 0:
            scores[doc_type] = matches / len(patterns)
    if not scores:
        return None
    best = max(scores, key=scores.get)
    return best, scores[best]


class KeywordClassifierTool(BaseTool):
    @property
    def name(self) -> str:
        return "keyword_classifier"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        ocr_result = context.get_result("ocr")
        text = ""
        if ocr_result and ocr_result.output:
            text = ocr_result.output.get("text", "")

        if not text:
            image_bytes = kwargs.get("image_bytes")
            if image_bytes:
                try:
                    from app.tools.paddleocr_tool import PaddleOCRTool
                    paddle = PaddleOCRTool()
                    r = await paddle.execute(context, image_bytes=image_bytes)
                    text = (r.output or {}).get("text", "")
                except Exception as e:
                    logger.warning(f"Quick OCR in classifier failed: {e}")

        if not text:
            return ToolResult(tool_name=self.name, output={"doc_type": "unknown"},
                              confidence=0.0, processing_time_ms=0.0)

        match = _keyword_match(text)
        if match:
            doc_type, score = match
            return ToolResult(
                tool_name=self.name,
                output={"doc_type": doc_type, "reasoning": f"keyword match score={score:.2f}"},
                confidence=min(score * 2.0, 0.95),
                processing_time_ms=0.0,
            )

        return ToolResult(tool_name=self.name, output={"doc_type": "unknown"},
                          confidence=0.1, processing_time_ms=0.0)


class VisualSimilarityTool(BaseTool):
    @property
    def name(self) -> str:
        return "visual_similarity"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        image_bytes: bytes = kwargs.get("image_bytes")
        templates: list = kwargs.get("available_templates", [])

        if not image_bytes or not templates:
            return ToolResult(tool_name=self.name, output={"doc_type": "unknown"},
                              confidence=0.0, processing_time_ms=0.0)

        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self._match, image_bytes, templates)
        return result

    def _match(self, image_bytes: bytes, templates: list) -> ToolResult:
        import numpy as np
        import cv2

        nparr = np.frombuffer(image_bytes, np.uint8)
        img_gray = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        orb = cv2.ORB_create()
        kp1, des1 = orb.detectAndCompute(img_gray, None)

        best_score = 0.0
        best_template = "unknown"

        for tpl in templates:
            if isinstance(tpl, dict):
                sample_url = tpl.get("sample_image_url")
                slug = tpl.get("slug", "unknown")
            else:
                sample_url = getattr(tpl, "sample_image_url", None)
                slug = getattr(tpl, "slug", "unknown")
                
            if not sample_url:
                continue
            try:
                import httpx
                resp = httpx.get(sample_url, timeout=5.0)
                tpl_arr = np.frombuffer(resp.content, np.uint8)
                tpl_gray = cv2.imdecode(tpl_arr, cv2.IMREAD_GRAYSCALE)
                kp2, des2 = orb.detectAndCompute(tpl_gray, None)
                if des1 is None or des2 is None:
                    continue
                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                matches = bf.match(des1, des2)
                score = len([m for m in matches if m.distance < 40]) / max(len(kp2), 1)
                if score > best_score:
                    best_score = score
                    best_template = slug
            except Exception:
                continue

        confidence = min(best_score * 5.0, 0.9)
        return ToolResult(
            tool_name=self.name,
            output={"doc_type": best_template, "similarity_score": best_score},
            confidence=confidence,
            processing_time_ms=0.0,
        )
