import pytest
from app.agents.base import AgentContext, ToolResult
from app.agents.scoring_agent import ScoringAgent


@pytest.fixture
def ctx_with_results():
    ctx = AgentContext()
    ctx.results["authenticity"] = ToolResult(
        tool_name="authenticity_aggregate",
        output={"authenticity_score": 85.0, "is_suspicious": False, "checks": []},
        confidence=0.85,
        processing_time_ms=0.0,
    )
    ctx.results["consistency"] = ToolResult(
        tool_name="consistency_checks",
        output={"consistency_score": 90.0, "flags": [], "checks": []},
        confidence=0.90,
        processing_time_ms=0.0,
    )
    return ctx


class TestScoringAgent:
    @pytest.mark.asyncio
    async def test_score_with_valid_cnas(self, ctx_with_results):
        agent = ScoringAgent()
        result = await agent.run(
            ctx_with_results,
            kyc_result={"passed": True, "liveness_score": 0.92},
            cnas_result={"valid": True},
            documents_submitted=["affiliation_attestation", "national_id"],
            required_docs=["affiliation_attestation"],
        )
        assert result.output["score"] > 70
        assert result.output["decision"] in ("approved", "review")
        assert result.output["blockers"] == []

    @pytest.mark.asyncio
    async def test_blocker_on_kyc_failure(self, ctx_with_results):
        agent = ScoringAgent()
        result = await agent.run(
            ctx_with_results,
            kyc_result={"passed": False, "liveness_score": 0.0},
            cnas_result={"valid": True},
            documents_submitted=["affiliation_attestation"],
            required_docs=["affiliation_attestation"],
        )
        assert result.output["score"] == 0.0
        assert result.output["decision"] == "rejected"
        assert any("KYC" in b for b in result.output["blockers"])

    @pytest.mark.asyncio
    async def test_blocker_on_very_low_authenticity(self):
        ctx = AgentContext()
        ctx.results["authenticity"] = ToolResult(
            tool_name="authenticity_aggregate",
            output={"authenticity_score": 15.0, "is_suspicious": True, "checks": []},
            confidence=0.15,
            processing_time_ms=0.0,
        )
        agent = ScoringAgent()
        result = await agent.run(
            ctx,
            kyc_result={"passed": True, "liveness_score": 0.9},
            documents_submitted=["national_id"],
            required_docs=[],
        )
        assert result.output["score"] == 0.0
        assert result.output["decision"] == "rejected"

    @pytest.mark.asyncio
    async def test_soft_flag_on_failed_cnas(self, ctx_with_results):
        agent = ScoringAgent()
        result = await agent.run(
            ctx_with_results,
            kyc_result={"passed": True, "liveness_score": 0.88},
            cnas_result={"valid": False},
            documents_submitted=["affiliation_attestation"],
            required_docs=[],
        )
        assert result.output["decision"] in ("review", "rejected")
        assert any("CNAS" in f["message"] for f in result.output["flags"])

    @pytest.mark.asyncio
    async def test_optional_doc_bonus(self, ctx_with_results):
        agent = ScoringAgent()
        result_no_bonus = await agent.run(
            ctx_with_results,
            kyc_result={"passed": True, "liveness_score": 0.9},
            cnas_result={"valid": True},
            documents_submitted=["affiliation_attestation"],
            required_docs=["affiliation_attestation"],
        )
        result_with_bonus = await agent.run(
            ctx_with_results,
            kyc_result={"passed": True, "liveness_score": 0.9},
            cnas_result={"valid": True},
            documents_submitted=["affiliation_attestation", "diploma", "national_id"],
            required_docs=["affiliation_attestation"],
        )
        assert result_with_bonus.output["score"] >= result_no_bonus.output["score"]

    @pytest.mark.asyncio
    async def test_result_stored_in_context(self, ctx_with_results):
        agent = ScoringAgent()
        await agent.run(ctx_with_results)
        assert "scoring" in ctx_with_results.results
