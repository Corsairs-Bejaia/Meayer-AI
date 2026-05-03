import logging
from typing import List, Dict, Any

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.tools.gemini_tool import GeminiVisionTool

logger = logging.getLogger(__name__)

class ReportAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "report"

    @property
    def tools(self) -> List[BaseTool]:
        return []

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        # Extract summary of all results for the prompt
        summary_data = {
            "verification_id": context.verification_id,
            "steps": []
        }
        
        for step, res in context.results.items():
            summary_data["steps"].append({
                "agent": step,
                "confidence": res.confidence,
                "output_summary": str(res.output)[:500] # Truncated
            })
            
        scoring = context.get_result("scoring")
        if scoring:
            summary_data["final_decision"] = scoring.output.get("decision")
            summary_data["final_score"] = scoring.output.get("score")
            summary_data["blockers"] = scoring.output.get("blockers")

        prompt = (
            f"Generate a professional, structured verification report based on these execution steps: {summary_data}. "
            "The report should be in Markdown, clearly explaining the trust layers validated, "
            "any authenticity flags raised, and the final decision. "
            "Use a tone suitable for a medical administrative dashboard. "
            "Keep it concise but informative."
        )

        try:
            # We use Gemini to generate the text
            gemini = GeminiVisionTool()
            # We pass a dummy empty image or just text-only if supported by the tool
            # Our current GeminiVisionTool expects image_bytes, let's fix it to allow text-only or use a placeholder
            res = await gemini.execute(context, prompt=prompt, image_bytes=kwargs.get("image_bytes"))
            
            report_text = res.output.get("text", "Report generation failed.") if res.output else "Report generation failed."
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            report_text = f"Automatic report generation failed. Decision: {summary_data.get('final_decision')}"

        result = ToolResult(
            tool_name="report_generation",
            output={"report_md": report_text},
            confidence=1.0,
            processing_time_ms=0.0
        )
        context.results[self.name] = result
        return result
