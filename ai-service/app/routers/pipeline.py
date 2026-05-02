import json
import time
import logging
import asyncio
from typing import AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.agents.base import AgentContext
from app.agents.orchestrator import AgentOrchestrator
from app.dependencies import verify_api_key
from app.schemas.schemas import PipelineRequest, PipelineResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
_orchestrator = AgentOrchestrator()


@router.post(
    ,
    summary="Run Full Agentic Pipeline",
    description=(
        
        
    ),
)
async def run_pipeline(
    request: PipelineRequest,
    _: str = Depends(verify_api_key),
):
    start_time = time.time()
    docs = [d.model_dump() for d in request.documents]
    templates = [t.model_dump() for t in request.templates]
    extra = {}
    if request.kyc_result:
        extra["kyc_result"] = request.kyc_result
    if request.cnas_result:
        extra["cnas_result"] = request.cnas_result
    if request.required_docs:
        extra["required_docs"] = request.required_docs

    
    if not request.stream:
        context = await _orchestrator.run_pipeline(
            documents=docs,
            templates=templates,
            extra_kwargs=extra,
        )
        elapsed = round((time.time() - start_time) * 1000, 1)
        return {
            : context.verification_id,
            : {k: v.output for k, v in context.results.items()},
            : context.trace,
            : elapsed,
        }

    
    async def event_stream() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue()

        async def progress_callback(step: str, status: str, result=None):
            payload = {"step": step, "status": status}
            if result and hasattr(result, "output"):
                payload["result"] = result.output
            elif isinstance(result, (dict, list)):
                payload["result"] = result
            await queue.put(payload)

        
        async def _run():
            try:
                context = await _orchestrator.run_pipeline(
                    documents=docs,
                    templates=templates,
                    progress_callback=progress_callback,
                    extra_kwargs=extra,
                )
                elapsed = round((time.time() - start_time) * 1000, 1)
                await queue.put({
                    : "complete",
                    : "done",
                    : context.verification_id,
                    : {k: v.output for k, v in context.results.items()},
                    : elapsed,
                })
            except Exception as e:
                logger.error(f"Pipeline error: {e}")
                await queue.put({"step": "error", "status": "failed", "error": str(e)})
            finally:
                await queue.put(None)  

        task = asyncio.create_task(_run())

        while True:
            item = await queue.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

        await task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            : "no-cache",
            : "no",
        },
    )
