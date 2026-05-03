import pytest
import io
from PIL import Image
from unittest.mock import AsyncMock, patch

from app.agents.base import AgentContext, ToolResult
from app.agents.classifier_agent import ClassifierAgent
from app.agents.extraction_agent import ExtractionAgent
from app.agents.authenticity_agent import AuthenticityAgent
from app.agents.consistency_agent import ConsistencyAgent
from app.agents.scoring_agent import ScoringAgent


def create_dummy_image(color=(255, 255, 255)):
    img = Image.new('RGB', (100, 100), color=color)
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return buf.getvalue()



class TestAgentPersonality:

    @pytest.mark.asyncio
    async def test_classifier_agent_tone_and_work(self):
        
        agent = ClassifierAgent()
        ctx = AgentContext()
        
        
        with patch("app.tools.classifier_tools.KeywordClassifierTool.execute", new_callable=AsyncMock) as mock_keyword:
            mock_keyword.return_value = ToolResult(
                tool_name="keyword_classifier",
                output={"doc_type": "national_id", "reasoning": "keyword match score=0.8"},
                confidence=0.9,
                processing_time_ms=10.0
            )
            
            result = await agent.run(ctx, image_bytes=create_dummy_image())
            
            assert result.output["doc_type"] == "national_id"
            assert result.confidence >= 0.7
            assert "keyword" in result.tool_name
            
            assert any(t["agent"] == "classifier" for t in ctx.trace)

    @pytest.mark.asyncio
    async def test_extraction_agent_work(self):
        
        agent = ExtractionAgent()
        ctx = AgentContext()
        fields = [
            {"field_name": "full_name", "is_required": True},
            {"field_name": "nin", "is_required": True, "validation_regex": "^\\d{18}$"}
        ]
        
        
        with patch("app.tools.extraction_tools.PositionalExtractorTool.execute", new_callable=AsyncMock) as mock_pos,             patch("app.tools.extraction_tools.RegexExtractorTool.execute", new_callable=AsyncMock) as mock_reg,             patch("app.tools.gemini_tool.GeminiExtractorTool.execute", new_callable=AsyncMock) as mock_gem:
            
            mock_pos.return_value = ToolResult("positional", {"fields": {}}, 0.0, 0.0)
            mock_reg.return_value = ToolResult("regex", {"fields": {"full_name": {"value": "John Doe", "confidence": 0.9}}}, 0.5, 0.0)
            mock_gem.return_value = ToolResult("gemini", {"fields": {"nin": {"value": "123456789012345678", "confidence": 0.95}}}, 0.95, 0.0)
            
            result = await agent.run(ctx, image_bytes=create_dummy_image(), fields=fields, doc_type="national_id")
            
            extracted = result.output["extracted_fields"]
            assert extracted["full_name"]["value"] == "John Doe"
            assert extracted["nin"]["value"] == "123456789012345678"
            assert result.confidence > 0.8

    @pytest.mark.asyncio
    async def test_authenticity_agent_parallel_work(self):
        
        agent = AuthenticityAgent()
        ctx = AgentContext()
        
        
        
        with patch.object(agent._ela, 'execute', new_callable=AsyncMock) as m_ela,             patch.object(agent._stamp, 'execute', new_callable=AsyncMock) as m_stamp,             patch.object(agent._signature, 'execute', new_callable=AsyncMock) as m_sig,             patch.object(agent._photocopy, 'execute', new_callable=AsyncMock) as m_photo:
            
            m_ela.return_value = ToolResult("ela_analysis", {"tampering_detected": False}, 0.95, 0.0)
            m_stamp.return_value = ToolResult("stamp_detector", {"detected": True}, 0.9, 0.0)
            m_sig.return_value = ToolResult("signature_detector", {"detected": True}, 0.85, 0.0)
            m_photo.return_value = ToolResult("photocopy_detector", {"is_photocopy": False}, 0.9, 0.0)
            
            result = await agent.run(ctx, image_bytes=create_dummy_image())
            
            assert "authenticity_score" in result.output
            assert result.output["is_suspicious"] is False
            assert len(result.output["checks"]) >= 4

    @pytest.mark.asyncio
    async def test_consistency_agent_logic(self):
        
        agent = ConsistencyAgent()
        ctx = AgentContext()
        
        
        
        documents = {
            "national_id": {"nin": "900101123456789012", "full_name": "John Doe", "date_of_birth": "1990-01-01"},
            "diplome_medecine": {"full_name": "Jane Smith"}
        }
        
        result = await agent.run(ctx, documents=documents)
        
        
        assert result.output["consistency_score"] < 100 
        assert any(f["check"] == "name_consistency" for f in result.output["flags"])
        assert any(c["check"] == "nin_dob_match" and c["passed"] for c in result.output["checks"])

    @pytest.mark.asyncio
    async def test_scoring_agent_final_decision(self):
        
        agent = ScoringAgent()
        ctx = AgentContext()
        
        
        ctx.results["authenticity"] = ToolResult("auth", {"authenticity_score": 95.0}, 0.95, 0.0)
        ctx.results["consistency"] = ToolResult("cons", {"consistency_score": 90.0, "flags": []}, 0.9, 0.0)
        ctx.results["extraction"] = ToolResult("extr", {"extracted_fields": {"diploma_specialty": "CS"}}, 0.9, 0.0)
        
        result = await agent.run(ctx, 
                                 kyc_result={"passed": True, "liveness_score": 0.98},
                                 cnas_result={"valid": True},
                                 documents_submitted=["national_id", "diploma", "attestation_ordre", "affiliation_attestation", "carte_chifa"],
                                 required_docs=["national_id", "diploma"])
        
        assert result.output["score"] > 70
        assert result.output["decision"] in ("approved", "review")
        
        assert "layers_covered" in result.output["documents_coverage"]

    def test_agent_tone_assertion(self):
        
        
        pass
