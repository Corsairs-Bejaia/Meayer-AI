import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.orchestrator import AgentOrchestrator
from app.agents.base import AgentContext, ToolResult


def create_dummy_doc(index):
    return {
        : f"http://example.com/doc{index}.jpg",
        : "national_id" if index == 0 else "diploma"
    }



class TestAgentOrchestrator:

    @pytest.mark.asyncio
    async def test_full_pipeline_success(self):
        
        orchestrator = AgentOrchestrator()
        documents = [create_dummy_doc(0), create_dummy_doc(1)]
        templates = [
            {"slug": "dz-national-id-v1", "doc_type": "national_id", "fields": [{"field_name": "full_name"}]},
            {"slug": "dz-university-diploma-v1", "doc_type": "diploma", "fields": [{"field_name": "university"}]}
        ]
        
        
        with patch("app.agents.orchestrator._fetch_image", new_callable=AsyncMock) as mock_fetch,             patch.object(orchestrator.classifier, "run", new_callable=AsyncMock) as m_class,             patch.object(orchestrator.ocr, "run", new_callable=AsyncMock) as m_ocr,             patch.object(orchestrator.extraction, "run", new_callable=AsyncMock) as m_extr,             patch.object(orchestrator.authenticity, "run", new_callable=AsyncMock) as m_auth,             patch.object(orchestrator.consistency, "run", new_callable=AsyncMock) as m_cons,             patch.object(orchestrator.scoring, "run", new_callable=AsyncMock) as m_score:
            
            mock_fetch.return_value = b"fake_image_bytes"
            
            
            m_class.return_value = ToolResult("classifier", {"doc_type": "national_id"}, 0.9, 0.0)
            m_ocr.return_value = ToolResult("ocr", {"text": "some text"}, 0.9, 0.0)
            m_extr.return_value = ToolResult("extraction", {"extracted_fields": {"full_name": "John Doe"}}, 0.9, 0.0)
            m_auth.return_value = ToolResult("authenticity", {"authenticity_score": 90.0}, 0.9, 0.0)
            m_cons.return_value = ToolResult("consistency", {"consistency_score": 100.0}, 1.0, 0.0)
            m_score.return_value = ToolResult("scoring", {"score": 95.0, "decision": "approved"}, 1.0, 0.0)

            
            progress_updates = []
            async def progress_callback(step, status, result):
                progress_updates.append((step, status))

            context = await orchestrator.run_pipeline(
                documents=documents,
                templates=templates,
                progress_callback=progress_callback,
                extra_kwargs={"kyc_result": {"passed": True}}
            )

            assert context is not None
            assert len(progress_updates) > 5
            assert progress_updates[-1][0] == "complete"
            
            
            m_cons.assert_called_once()
            call_kwargs = m_cons.call_args.kwargs
            assert "documents" in call_kwargs
            assert len(call_kwargs["documents"]) > 0

    @pytest.mark.asyncio
    async def test_pipeline_with_fetch_error(self):
        
        orchestrator = AgentOrchestrator()
        documents = [create_dummy_doc(0), create_dummy_doc(1)]
        
        with patch("app.agents.orchestrator._fetch_image", new_callable=AsyncMock) as mock_fetch:
            
            mock_fetch.side_effect = [b"valid_bytes", Exception("Network error")]
            
            
            with patch.object(orchestrator.classifier, "run", new_callable=AsyncMock) as m_class,                 patch.object(orchestrator.ocr, "run", new_callable=AsyncMock) as m_ocr,                 patch.object(orchestrator.extraction, "run", new_callable=AsyncMock) as m_extr,                 patch.object(orchestrator.authenticity, "run", new_callable=AsyncMock) as m_auth,                 patch.object(orchestrator.consistency, "run", new_callable=AsyncMock) as m_cons,                 patch.object(orchestrator.scoring, "run", new_callable=AsyncMock) as m_score:
                
                m_class.return_value = ToolResult("classifier", {"doc_type": "unknown"}, 0.0, 0.0)
                m_ocr.return_value = ToolResult("ocr", {"text": ""}, 0.0, 0.0)
                m_extr.return_value = ToolResult("extraction", {"extracted_fields": {}}, 0.0, 0.0)
                m_auth.return_value = ToolResult("authenticity", {"authenticity_score": 0.0}, 0.0, 0.0)
                m_cons.return_value = ToolResult("consistency", {"consistency_score": 0.0}, 0.0, 0.0)
                m_score.return_value = ToolResult("scoring", {"score": 0.0, "decision": "rejected"}, 0.0, 0.0)

                context = await orchestrator.run_pipeline(documents=documents)
                
                assert context is not None
                
                assert m_class.call_count == 2 

    @pytest.mark.asyncio
    async def test_scoring_with_blockers(self):
        
        from app.agents.scoring_agent import ScoringAgent
        agent = ScoringAgent()
        ctx = AgentContext()
        
        
        ctx.results["consistency"] = ToolResult("consistency", {
            : 10.0,
            : [{"type": "hard", "message": "NIN mismatch"}]
        }, 1.0, 0.0)
        
        result = await agent.run(ctx, documents_submitted=["id"], required_docs=["id"])
        
        assert result.output["score"] == 0.0
        assert result.output["decision"] == "rejected"
        assert "NIN mismatch" in result.output["blockers"]
