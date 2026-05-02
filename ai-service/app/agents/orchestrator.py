import asyncio
import logging
import httpx
from typing import Any, Callable, Awaitable, Dict, List, Optional

from app.agents.base import AgentContext, ToolResult
from app.agents.classifier_agent import ClassifierAgent
from app.agents.ocr_agent import OCRAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.authenticity_agent import AuthenticityAgent
from app.agents.consistency_agent import ConsistencyAgent
from app.agents.scoring_agent import ScoringAgent

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, str, Any], Awaitable[None]]


async def _fetch_image(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content


class AgentOrchestrator:
    def __init__(self):
        self.classifier = ClassifierAgent()
        self.ocr = OCRAgent()
        self.extraction = ExtractionAgent()
        self.authenticity = AuthenticityAgent()
        self.consistency = ConsistencyAgent()
        self.scoring = ScoringAgent()

    async def run_pipeline(
        self,
        documents: List[Dict[str, Any]],
        templates: Optional[List[Dict]] = None,
        progress_callback: Optional[ProgressCallback] = None,
        extra_kwargs: Optional[Dict] = None,
    ) -> AgentContext:
        context = AgentContext(documents=documents)
        templates = templates or []
        extra_kwargs = extra_kwargs or {}

        async def _emit(step: str, status: str, result: Any = None):
            if progress_callback:
                try:
                    await progress_callback(step, status, result)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")

        doc_bytes: Dict[int, bytes] = {}
        for i, doc in enumerate(documents):
            url = doc.get("file_url")
            if url:
                try:
                    doc_bytes[i] = await _fetch_image(url)
                except Exception as e:
                    logger.warning(f"Failed to fetch document {i} from {url}: {e}")

        await _emit("classification", "started")
        classify_tasks = [
            self.classifier.run(
                context,
                image_bytes=doc_bytes.get(i),
                available_templates=templates,
            )
            for i, doc in enumerate(documents)
        ]
        classification_results = await asyncio.gather(*classify_tasks, return_exceptions=True)
        await _emit("classification", "completed", context.get_result("classifier"))

        await _emit("ocr_extraction", "started")

        async def _ocr_and_extract(i: int, doc: Dict) -> Dict:
            image_bytes = doc_bytes.get(i)
            if not image_bytes:
                return {}

            doc_type = doc.get("doc_type_hint") or (
                context.get_result("classifier").output.get("doc_type")
                if context.get_result("classifier") else "unknown"
            )
            template = next(
                (t for t in templates if t.get("slug") == doc.get("template_slug")
                 or t.get("doc_type") == doc_type),
                {}
            )
            fields = template.get("fields", [])

            ocr_result = await self.ocr.run(context, image_bytes=image_bytes)

            extraction_result = await self.extraction.run(
                context,
                image_bytes=image_bytes,
                fields=fields,
                doc_type=doc_type,
            )
            return {
                "doc_index": i,
                "doc_type": doc_type,
                "ocr": ocr_result.output,
                "extraction": extraction_result.output,
            }

        extraction_tasks = [
            _ocr_and_extract(i, doc)
            for i, doc in enumerate(documents)
        ]
        per_doc_results = await asyncio.gather(*extraction_tasks, return_exceptions=True)
        per_doc_results = [r for r in per_doc_results if isinstance(r, dict)]
        await _emit("ocr_extraction", "completed", per_doc_results)

        await _emit("authenticity", "started")
        auth_tasks = [
            self.authenticity.run(context, image_bytes=doc_bytes.get(i))
            for i, doc in enumerate(documents)
            if doc_bytes.get(i)
        ]
        await asyncio.gather(*auth_tasks, return_exceptions=True)
        await _emit("authenticity", "completed", context.get_result("authenticity"))

        await _emit("consistency", "started")
        documents_fields: Dict[str, Dict] = {}
        for r in per_doc_results:
            if isinstance(r, dict):
                dt = r.get("doc_type", "unknown")
                documents_fields[dt] = r.get("extraction", {}).get("extracted_fields", {})

        await self.consistency.run(context, documents=documents_fields)
        await _emit("consistency", "completed", context.get_result("consistency"))

        await _emit("scoring", "started")
        await self.scoring.run(
            context,
            documents_submitted=[d.get("doc_type_hint", "unknown") for d in documents],
            **extra_kwargs,
        )
        await _emit("scoring", "completed", context.get_result("scoring"))
        await _emit("complete", "done", {
            k: v.output for k, v in context.results.items()
        })

        return context
