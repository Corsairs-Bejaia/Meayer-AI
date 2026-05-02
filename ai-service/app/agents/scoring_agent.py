import logging
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.services.layer_registry import (
    LAYER_DEFINITIONS,
    DOC_TYPE_TO_LAYER,
    group_docs_by_layer,
    get_missing_layers
)

logger = logging.getLogger(__name__)


class ScoringAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "scoring"

    @property
    def tools(self) -> List[BaseTool]:
        return []

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        kyc_result: Optional[Dict] = kwargs.get("kyc_result")
        cnas_result: Optional[Dict] = kwargs.get("cnas_result")
        casnos_result: Optional[Dict] = kwargs.get("casnos_result")
        documents_submitted: List[str] = kwargs.get("documents_submitted", [])
        required_docs: List[str] = kwargs.get("required_docs", [])
        per_doc_results: List[Dict] = kwargs.get("per_doc_results", [])

        # 1. Get results from previous agents
        authenticity_result = context.get_result("authenticity")
        consistency_result = context.get_result("consistency")
        extraction_result = context.get_result("extraction")

        # 2. Group documents by layer
        docs_by_layer = group_docs_by_layer(documents_submitted)
        missing_layers = get_missing_layers(documents_submitted)

        blockers: List[str] = []
        flags: List[Dict] = []
        layer_scores: Dict[str, Dict] = {}

        # 3. Calculate scores for each layer
        for lid, defn in LAYER_DEFINITIONS.items():
            layer_docs = docs_by_layer.get(lid, [])
            is_satisfied = len(layer_docs) >= defn["required_min"]
            
            # Base score for satisfying requirements
            if defn["required_min"] == 0:
                # Optional layer (L6)
                score = min(100.0, len(layer_docs) * 50.0)
            else:
                score = 100.0 if is_satisfied else (len(layer_docs) / defn["required_min"] * 80.0)

            # Adjustments based on quality/validation
            if lid == "L1": # Identity
                if kyc_result:
                    kyc_score = 100.0 if kyc_result.get("passed") else 0.0
                    score = (score * 0.4) + (kyc_score * 0.6)
                if not is_satisfied:
                    blockers.append("L1: Identity document missing")

            elif lid == "L2": # Academic
                if not is_satisfied:
                    blockers.append("L2: Academic qualification (Diploma) missing")

            elif lid == "L3": # Standing
                if not is_satisfied:
                    blockers.append("L3: Professional standing (Carte/Attestation Ordre) missing")

            elif lid == "L4": # Employment
                if cnas_result:
                    cnas_score = 100.0 if cnas_result.get("valid") else 40.0
                    score = (score * 0.5) + (cnas_score * 0.5)

            elif lid == "L5": # Coverage
                if casnos_result:
                    casnos_score = 100.0 if casnos_result.get("valid") else 40.0
                    score = (score * 0.5) + (casnos_score * 0.5)

            layer_scores[lid] = {
                "layer": lid,
                "name": defn["name"],
                "score": round(score, 1),
                "weight": defn["weight"],
                "documents_submitted": layer_docs,
                "documents_required": defn["required_min"],
                "is_satisfied": is_satisfied,
            }

        # 4. Consistency & Authenticity penalties
        if consistency_result and consistency_result.output:
            c_score = consistency_result.output.get("consistency_score", 100.0)
            if c_score < 70.0:
                flags.append({"type": "hard", "message": f"Low cross-document consistency ({c_score}%)"})
            for flag in consistency_result.output.get("flags", []):
                flags.append(flag)

        if authenticity_result and authenticity_result.output:
            a_score = authenticity_result.output.get("authenticity_score", 100.0)
            if a_score < 80.0:
                flags.append({"type": "hard", "message": f"Suspicious document authenticity ({a_score}%)"})

        # 5. Final weighted score
        final_score = 0.0
        if not blockers:
            for lid, ls in layer_scores.items():
                final_score += ls["score"] * ls["weight"]
            
            # Apply consistency penalty to final score
            if consistency_result:
                c_conf = consistency_result.confidence
                final_score *= (0.8 + 0.2 * c_conf)

        # 6. Aggregate results
        coverage = {
            "total_submitted": len(documents_submitted),
            "layers_covered": sum(1 for ls in layer_scores.values() if ls["is_satisfied"]),
            "layers_total": len(LAYER_DEFINITIONS),
            "missing_layers": [m["name"] for m in missing_layers],
        }

        result = ToolResult(
            tool_name="multi_layer_scoring",
            output={
                "score": round(final_score, 1),
                "layer_scores": layer_scores,
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
