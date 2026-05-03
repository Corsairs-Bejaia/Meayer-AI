import logging
import asyncio
from google import genai
from app.agents.base import BaseTool, ToolResult, AgentContext
from app.config import settings

logger = logging.getLogger(__name__)

class GeminiVisionTool(BaseTool):
    

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
                confidence=0.95,
                processing_time_ms=0.0
            )
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error=str(e))

class GeminiOCRTool(GeminiVisionTool):
    
    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        prompt = (
            
            
            
        )
        kwargs["prompt"] = prompt
        result = await super().execute(context, **kwargs)
        return result

class GeminiExtractorTool(GeminiVisionTool):
    
    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        doc_type = kwargs.get("doc_type", "document")
        fields = kwargs.get("fields", [])
        missing = kwargs.get("missing_fields", fields)
        
        
        field_names = []
        for f in missing:
            if isinstance(f, dict):
                name = f.get("field_name")
                desc = f.get("description", "")
            else:
                name = getattr(f, "field_name", "unknown")
                desc = getattr(f, "description", "")
            field_names.append(f"- {name}: {desc}")
            
        field_descriptions = "\n".join(field_names)
        
        prompt = (
            f"You are a data extraction expert for Algerian documents. Type: {doc_type}. "
            
            
            
            f"Fields to extract:\n{field_descriptions}"
        )
        kwargs["prompt"] = prompt
        result = await super().execute(context, **kwargs)
        
        if result.output and "text" in result.output:
            try:
                import json
                import re
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
