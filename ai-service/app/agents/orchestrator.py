from app.agents.base import AgentContext, ToolResult
from app.agents.classifier_agent import ClassifierAgent
from app.agents.ocr_agent import OCRAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.authenticity_agent import AuthenticityAgent
from app.agents.consistency_agent import ConsistencyAgent
from app.agents.scoring_agent import ScoringAgent
import logging
from typing import List, Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)

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
        progress_callback: Callable[[str, str, Any], Awaitable[None]] = None
    ) -> AgentContext:
        context = AgentContext(documents=documents)
        
        # Phase 1: Classification
        if progress_callback: await progress_callback("classification", "started", None)
        await self.classifier.run(context)
        if progress_callback: await progress_callback("classification", "completed", context.get_result("classifier"))
        
        # Phase 2: OCR
        if progress_callback: await progress_callback("ocr", "started", None)
        await self.ocr.run(context)
        if progress_callback: await progress_callback("ocr", "completed", context.get_result("ocr"))
        
        # Phase 3: Extraction
        if progress_callback: await progress_callback("extraction", "started", None)
        await self.extraction.run(context)
        if progress_callback: await progress_callback("extraction", "completed", context.get_result("extraction"))
        
        # Phase 4: Authenticity
        if progress_callback: await progress_callback("authenticity", "started", None)
        await self.authenticity.run(context)
        if progress_callback: await progress_callback("authenticity", "completed", context.get_result("authenticity"))
        
        # Phase 5: Consistency
        if progress_callback: await progress_callback("consistency", "started", None)
        await self.consistency.run(context)
        if progress_callback: await progress_callback("consistency", "completed", context.get_result("consistency"))
        
        # Phase 6: Scoring
        if progress_callback: await progress_callback("scoring", "started", None)
        await self.scoring.run(context)
        if progress_callback: await progress_callback("scoring", "completed", context.get_result("scoring"))
        
        return context
