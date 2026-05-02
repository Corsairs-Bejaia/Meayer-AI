from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from app.agents.orchestrator import AgentOrchestrator
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import asyncio

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
orchestrator = AgentOrchestrator()

class PipelineRequest(BaseModel):
    documents: List[Dict[str, Any]]
    stream: bool = False

@router.post("")
async def run_pipeline(request: PipelineRequest):
    if not request.stream:
        context = await orchestrator.run_pipeline(request.documents)
        return {
            "verification_id": context.verification_id,
            "results": {k: v.output for k, v in context.results.items()},
            "trace": context.trace
        }
    
    async def event_generator():
        async def progress_callback(step: str, status: str, result: Any):
            data = json.dumps({
                "step": step,
                "status": status,
                "result": result.output if hasattr(result, 'output') else result
            })
            # yield f"data: {data}\n\n"
            # Note: StreamingResponse in FastAPI needs careful handling of yield
            pass

        # For SSE, we need a queue or similar to pipe results from orchestrator
        # For this hackathon version, we'll just yield at major steps
        # This is a simplified SSE implementation
        yield f"data: {json.dumps({'step': 'pipeline', 'status': 'started'})}\n\n"
        context = await orchestrator.run_pipeline(request.documents)
        yield f"data: {json.dumps({'step': 'pipeline', 'status': 'completed', 'results': {k: v.output for k, v in context.results.items()}})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
