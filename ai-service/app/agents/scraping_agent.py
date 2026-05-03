import logging
from typing import List, Dict, Any, Optional

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.services.cnas_scraper import scrape_cnas

logger = logging.getLogger(__name__)

class CNASScrapingTool(BaseTool):
    @property
    def name(self) -> str:
        return "cnas_scraper"

    async def execute(self, context: AgentContext, **kwargs) -> ToolResult:
        attestation_number = kwargs.get("attestation_number")
        employer_number = kwargs.get("employer_number")
        ssn = kwargs.get("ssn")

        if not attestation_number or not employer_number:
            return ToolResult(
                tool_name=self.name,
                output={"valid": False, "status": "missing_data", "message": "Missing required CNAS data for scraping."},
                confidence=1.0,
                processing_time_ms=0.0
            )

        logger.info(f"Starting CNAS scraping for Attestation: {attestation_number}, Employer: {employer_number}")
        try:
            result = await scrape_cnas(
                attestation_number=attestation_number,
                employer_number=employer_number,
                ssn=ssn
            )
            
            # The scrape_cnas returns dict with valid, status, employee_found, etc.
            confidence = 1.0 if result.get("valid") else 0.8
            return ToolResult(
                tool_name=self.name,
                output=result,
                confidence=confidence,
                processing_time_ms=result.get("processing_time_ms", 0)
            )
        except Exception as e:
            logger.error(f"CNAS Scraping failed: {e}")
            return ToolResult(
                tool_name=self.name,
                output={"valid": False, "status": "error", "error": str(e)},
                confidence=0.0,
                processing_time_ms=0.0,
                error=str(e)
            )

class ScrapingAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "scraping"

    @property
    def tools(self) -> List[BaseTool]:
        return [CNASScrapingTool()]

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        # Check extraction results for CNAS data
        extraction_res = context.get_result("extraction")
        
        cnas_data = {}
        if extraction_res and extraction_res.output:
            fields = extraction_res.output.get("fields", {})
            cnas_data = fields.get("attestation_affiliation_cnas", {})
            
        attestation_number = cnas_data.get("reference_number") or kwargs.get("attestation_number")
        employer_number = cnas_data.get("employer_id") or kwargs.get("employer_number")
        ssn = cnas_data.get("nin") or kwargs.get("ssn")

        # Fallback to check other documents for NIN if not found in CNAS document
        if not ssn and extraction_res and extraction_res.output:
            fields = extraction_res.output.get("fields", {})
            for doc_type, doc_fields in fields.items():
                if "nin" in doc_fields and doc_fields["nin"]:
                    ssn = doc_fields["nin"]
                    break

        if not attestation_number or not employer_number:
            result = ToolResult(
                tool_name="skip_scraping",
                output={"valid": False, "status": "skipped", "message": "No CNAS Attestation data found to scrape."},
                confidence=1.0,
                processing_time_ms=0.0
            )
            context.results[self.name] = result
            return result

        tool = self.tools[0]
        result = await tool.execute(
            context, 
            attestation_number=attestation_number, 
            employer_number=employer_number, 
            ssn=ssn
        )
        
        context.add_trace(self.name, tool.name, result.confidence, str(result.output)[:200])
        context.results[self.name] = result
        return result
