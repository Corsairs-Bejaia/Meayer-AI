import logging
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext

logger = logging.getLogger(__name__)


class ScoringAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "scoring"

    @property
    def tools(self) -> List[BaseTool]:
        return []

    TIER_WEIGHTS = {
        "identity": 0.30,
        "employment": 0.25,
        "credentials": 0.25,
        "document_integrity": 0.20,
    }

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        kyc_result: Optional[Dict] = kwargs.get("kyc_result")
        cnas_result: Optional[Dict] = kwargs.get("cnas_result")
        documents_submitted: List[str] = kwargs.get("documents_submitted", [])
        required_docs: List[str] = kwargs.get("required_docs", [])

        authenticity_result = context.get_result("authenticity")
        consistency_result = context.get_result("consistency")
        extraction_result = context.get_result("extraction")
        classifier_result = context.get_result("classifier")

        blockers: List[str] = []
        flags: List[Dict] = []
        tier_scores: Dict[str, Dict] = {}

        if classifier_result and classifier_result.output:
            doc_type = classifier_result.output.get("doc_type", "unknown")
            if doc_type == "unknown":
                blockers.append("Irrelevant document uploaded (not a recognized ID or Diploma)")
        elif not classifier_result:
             flags.append({"type": "info", "message": "Document classification not performed"})

        kyc_score = 0.0
        if kyc_result:
            kyc_passed = kyc_result.get("passed", False)
            kyc_liveness = float(kyc_result.get("liveness_score", 0.0))
            if not kyc_passed:
                blockers.append("KYC verification failed")
                kyc_score = 0.0
            else:
                kyc_score = kyc_liveness * 100
        else:
            kyc_score = 50.0
        tier_scores["identity"] = {
            "score": round(kyc_score, 1),
            "weight": self.TIER_WEIGHTS["identity"],
            "details": kyc_result or "KYC not provided",
        }

        employment_score = 0.0
        if cnas_result:
            cnas_valid = cnas_result.get("valid", False)
            employment_score = 90.0 if cnas_valid else 30.0
            if not cnas_valid:
                flags.append({"type": "soft", "message": "CNAS verification failed — manual review needed"})
        else:
            employment_score = 50.0
            flags.append({"type": "info", "message": "CNAS not verified"})
        tier_scores["employment"] = {
            "score": round(employment_score, 1),
            "weight": self.TIER_WEIGHTS["employment"],
            "details": cnas_result or "CNAS not provided",
        }

        credential_score = 50.0
        if extraction_result and extraction_result.output:
            extracted = extraction_result.output.get("extracted_fields", {})
            has_diploma_info = any(
                k in extracted for k in ("diploma_specialty", "graduation_year", "university")
            )
            credential_score = extraction_result.confidence * 100 if has_diploma_info else 50.0
        tier_scores["credentials"] = {
            "score": round(credential_score, 1),
            "weight": self.TIER_WEIGHTS["credentials"],
            "details": "Based on extraction confidence",
        }

        integrity_score = 50.0
        if authenticity_result and authenticity_result.output:
            integrity_score = authenticity_result.output.get("authenticity_score", 50.0)
            checks = authenticity_result.output.get("checks", [])
            
            ai_gen_check = next((c for c in checks if c["check"] == "ai_generation_detector"), None)
            if ai_gen_check and ai_gen_check["details"] and ai_gen_check["details"].get("is_ai_generated"):
                blockers.append(f"Synthetic Document Detected (AI Generated): {ai_gen_check['details'].get('reasoning')}")
                integrity_score = 0.0

            if integrity_score < 20 and not blockers:
                blockers.append("All documents failed authenticity check")
            elif integrity_score < 50:
                flags.append({"type": "soft", "message": f"Document authenticity score low: {integrity_score}"})
        tier_scores["document_integrity"] = {
            "score": round(integrity_score, 1),
            "weight": self.TIER_WEIGHTS["document_integrity"],
            "details": authenticity_result.output if authenticity_result else "Not checked",
        }

        if consistency_result and consistency_result.output:
            cons_score = consistency_result.output.get("consistency_score", 100.0)
            hard_flags = [f for f in consistency_result.output.get("flags", []) if f.get("type") == "hard"]
            if hard_flags:
                blockers.extend(f["message"] for f in hard_flags)
            if cons_score < 50:
                flags.append({"type": "soft", "message": f"Low consistency score: {cons_score}"})

        if blockers:
            final_score = 0.0
        else:
            final_score = sum(
                tier_scores[t]["score"] * self.TIER_WEIGHTS[t]
                for t in self.TIER_WEIGHTS
            )
            optional_submitted = [d for d in documents_submitted if d not in required_docs]
            final_score = min(100.0, final_score + len(optional_submitted) * 5)

        coverage = {
            "submitted": len(documents_submitted),
            "required_total": len(required_docs),
            "required_missing": [d for d in required_docs if d not in documents_submitted],
            "optional_submitted": [d for d in documents_submitted if d not in required_docs],
        }

        result = ToolResult(
            tool_name="tiered_scoring",
            output={
                "score": round(final_score, 1),
                "tier_scores": tier_scores,
                "blockers": blockers,
                "flags": flags,
                "documents_coverage": coverage,
                "decision": "rejected" if blockers else ("review" if flags else "approved"),
            },
            confidence=1.0,
            processing_time_ms=0.0,
        )
        context.results[self.name] = result
        return result
