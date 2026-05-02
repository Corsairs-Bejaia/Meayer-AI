import logging
import asyncio
from typing import Optional, Dict, Any
from google import genai
from app.agents.base import BaseTool, ToolResult, AgentContext
from app.config import settings

logger = logging.getLogger(__name__)

class GeminiVisionTool(BaseTool):
    """
    General purpose Vision tool using Gemini 2.0 Flash.
    Used for classification, OCR, and extraction when local tools fail.
    """

    @property
    def name(self) -> str:
        return "gemini_vision"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        if not settings.GEMINI_API_KEY or not settings.ENABLE_GEMINI_FALLBACK:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="Gemini disabled or no key")

        image_bytes: bytes = kwargs.get("image_bytes")
        prompt: str = kwargs.get("prompt", "Analyze this document.")

        if not image_bytes:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes")

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            # Run in executor to avoid blocking (SDK might be sync or async depending on version)
            # Current google-genai 1.0+ has async support but let's be safe
            loop = asyncio.get_event_loop()
            
            def _call():
                return client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=[prompt, image_bytes]
                )

            response = await loop.run_in_executor(None, _call)
            text = response.text.strip()
            
            return ToolResult(
                tool_name=self.name,
                output={"text": text},
                confidence=0.95, # Gemini is high confidence
                processing_time_ms=0.0
            )
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error=str(e))

class GeminiOCRTool(GeminiVisionTool):
    """
    OCR using Gemini Flash.
    """
    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        prompt = (
            "Perform high-accuracy OCR on this document. "
            "Return the full text. Preserve layout as much as possible. "
            "Handle both Arabic and French text."
        )
        kwargs["prompt"] = prompt
        result = await super().execute(context, **kwargs)
        # GeminiVisionTool already returns {"text": ...} in output
        return result

class GeminiExtractorTool(GeminiVisionTool):
    """
    Structured data extraction using Gemini Flash.
    """
    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        doc_type = kwargs.get("doc_type", "document")
        fields = kwargs.get("fields", [])
        missing = kwargs.get("missing_fields", fields)
        
        field_descriptions = "\n".join([f"- {f['field_name']}: {f.get('description', '')}" for f in missing])
        
        prompt = (
            f"You are a data extraction expert for Algerian documents. Type: {doc_type}. "
            "Extract the following fields from the image. "
            "Return ONLY a JSON object where keys are field names and values are strings. "
            "If a field is not found, return null for its value. "
            f"Fields to extract:\n{field_descriptions}"
        )
        kwargs["prompt"] = prompt
        result = await super().execute(context, **kwargs)
        
        if result.output and "text" in result.output:
            try:
                import json
                import re
                # Clean JSON markdown if present
                clean_json = re.sub(r"```json\n|\n```", "", result.output["text"]).strip()
                data = json.loads(clean_json)
                
                extracted = {}
                for k, v in data.items():
                    extracted[k] = {"value": v, "confidence": 0.9}
                
                result.output = {"fields": extracted}
            except Exception as e:
                logger.error(f"Failed to parse Gemini JSON: {e}")
                result.error = "JSON parse error"
        
        return result
