import asyncio
import base64
import logging
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from app.agents.base import BaseTool, ToolResult, AgentContext
from app.config import settings

logger = logging.getLogger(__name__)

_openai_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _bytes_to_data_url(image_bytes: bytes) -> str:
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


class GPT4oVisionOCRTool(BaseTool):
    """
    GPT-4o Vision as last-resort OCR. Handles low quality, handwritten,
    and complex mixed-language layouts. ~$0.01-0.03 per call.
    """

    @property
    def name(self) -> str:
        return "gpt4o_vision_ocr"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        if not settings.ENABLE_GPT4O_FALLBACK:
            return ToolResult(
                tool_name=self.name,
                output=None,
                confidence=0.0,
                processing_time_ms=0.0,
                error="GPT-4o fallback disabled",
            )

        image_bytes: bytes = kwargs.get("image_bytes")
        if not image_bytes:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes")

        try:
            client = _get_client()
            data_url = _bytes_to_data_url(image_bytes)

            response = await client.chat.completions.create(
                model="gpt-4o",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Extract ALL text from this Algerian document. "
                                    "Preserve the original layout and language (Arabic and/or French). "
                                    "Return the raw text exactly as it appears, with line breaks preserved."
                                ),
                            },
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
            )

            extracted_text = response.choices[0].message.content or ""
            # GPT-4o Vision OCR is assumed high confidence when it returns text
            confidence = 0.95 if extracted_text.strip() else 0.1

            return ToolResult(
                tool_name=self.name,
                output={"text": extracted_text, "avg_confidence": confidence},
                confidence=confidence,
                processing_time_ms=0.0,
            )

        except Exception as e:
            logger.error(f"GPT-4o OCR error: {e}")
            return ToolResult(
                tool_name=self.name, output=None, confidence=0.0,
                processing_time_ms=0.0, error=str(e),
            )


class GPT4oClassifierTool(BaseTool):
    """
    GPT-4o Vision for document type classification.
    """

    @property
    def name(self) -> str:
        return "gpt4o_classifier"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        if not settings.ENABLE_GPT4O_FALLBACK:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="GPT-4o disabled")

        image_bytes: bytes = kwargs.get("image_bytes")
        available_templates: list = kwargs.get("available_templates", [])

        if not image_bytes:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes")

        template_list = ", ".join(
            [f"{t.get('slug')} ({t.get('doc_type')})" for t in available_templates]
        ) or "national_id, diploma, affiliation_attestation, agreement, chifa, ordonnance"

        try:
            client = _get_client()
            data_url = _bytes_to_data_url(image_bytes)

            response = await client.chat.completions.create(
                model="gpt-4o",
                max_tokens=300,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"Classify this Algerian administrative document. "
                                    f"Choose from: {template_list}. "
                                    "Return JSON: {\"doc_type\": str, \"matched_template_slug\": str, "
                                    "\"confidence\": float (0-1), \"language\": \"ar\"|\"fr\"|\"ar+fr\", "
                                    "\"reasoning\": str}"
                                ),
                            },
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
            )

            import json
            content = response.choices[0].message.content or "{}"
            result = json.loads(content)
            confidence = float(result.get("confidence", 0.8))

            return ToolResult(
                tool_name=self.name,
                output=result,
                confidence=confidence,
                processing_time_ms=0.0,
            )

        except Exception as e:
            logger.error(f"GPT-4o classifier error: {e}")
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error=str(e))


class GPT4oExtractorTool(BaseTool):
    """
    GPT-4o Vision for structured field extraction from a document.
    """

    @property
    def name(self) -> str:
        return "gpt4o_extractor"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        if not settings.ENABLE_GPT4O_FALLBACK:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="GPT-4o disabled")

        image_bytes: bytes = kwargs.get("image_bytes")
        doc_type: str = kwargs.get("doc_type", "document")
        fields: list = kwargs.get("fields", [])
        missing_fields: list = kwargs.get("missing_fields")  # Re-extract specific fields

        if not image_bytes:
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error="No image_bytes")

        target_fields = missing_fields or fields
        field_descriptions = "\n".join(
            [f"- {f.get('field_name')}: {f.get('description', f.get('field_type', 'text'))}"
             for f in target_fields]
        )

        try:
            client = _get_client()
            data_url = _bytes_to_data_url(image_bytes)

            response = await client.chat.completions.create(
                model="gpt-4o",
                max_tokens=1000,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    f"Extract these fields from this {doc_type} document:\n"
                                    f"{field_descriptions}\n\n"
                                    "For each field return: {\"field_name\": {\"value\": ..., \"confidence\": 0-1}}. "
                                    "Return as JSON object. Use null for missing fields."
                                ),
                            },
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
            )

            import json
            content = response.choices[0].message.content or "{}"
            extracted = json.loads(content)

            # Calculate average confidence
            confidences = [
                v.get("confidence", 0.9)
                for v in extracted.values()
                if isinstance(v, dict) and v.get("value") is not None
            ]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

            return ToolResult(
                tool_name=self.name,
                output={"fields": extracted},
                confidence=avg_conf,
                processing_time_ms=0.0,
            )

        except Exception as e:
            logger.error(f"GPT-4o extractor error: {e}")
            return ToolResult(tool_name=self.name, output=None, confidence=0.0,
                              processing_time_ms=0.0, error=str(e))
