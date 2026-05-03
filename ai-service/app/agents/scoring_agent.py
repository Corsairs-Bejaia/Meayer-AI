import logging
from typing import Dict, List, Optional

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.services.layer_registry import LAYER_DEFINITIONS, DOC_TYPE_TO_LAYER

logger = logging.getLogger(__name__)


class ScoringAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "scoring"

    @property
    def tools(self) -> List[BaseTool]:
        return []

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        documents_submitted = kwargs.get("documents_submitted", [])
        kyc_result = kwargs.get("kyc_result") or {}
        cnas_result = kwargs.get("cnas_result") or {}
        casnos_result = kwargs.get("casnos_result") or {}
        consistency_result = context.get_result("consistency")
        authenticity_result = context.get_result("authenticity")
        
        layer_scores = {}
        for lid, defn in LAYER_DEFINITIONS.items():
            layer_docs = [d for d in documents_submitted if DOC_TYPE_TO_LAYER.get(d) == lid]
            
            # Simple saturation score
            score = (len(layer_docs) / defn["required_min"]) * 100 if defn["required_min"] > 0 else 100
            score = min(score, 100.0)
            
            is_satisfied = len(layer_docs) >= defn["required_min"]
            
            layer_scores[lid] = {
                "layer": lid,
                "name": defn["name"],
                "score": round(score, 1),
                "weight": defn["weight"],
                "documents_submitted": layer_docs,
                "documents_required": defn["required_min"],
                "is_satisfied": is_satisfied,
            }

        # Blockers
        blockers = []
        for lid in ["L1", "L2", "L3"]:
            if not layer_scores[lid]["is_satisfied"]:
                blockers.append(f"{lid}: {layer_scores[lid]['name']} document missing")

        # Flags
        flags = []
        if authenticity_result and authenticity_result.confidence < 0.6:
            flags.append({"type": "hard", "message": f"Suspicious document authenticity ({round(authenticity_result.confidence*100,1)}%)"})
        
        if consistency_result and not consistency_result.output.get("overall_consistent", True):
            for f in consistency_result.output.get("flags", []):
                flags.append(f)

        # Final Score Calculation
        final_score = 0.0
        for lid, ls in layer_scores.items():
            final_score += ls["score"] * ls["weight"]
            
        if consistency_result:
            c_conf = consistency_result.confidence
            final_score *= (0.8 + 0.2 * c_conf)

        # External data boosts
        if kyc_result.get("passed"): final_score = min(100, final_score + 5)
        if cnas_result.get("valid"): final_score = min(100, final_score + 5)
        if casnos_result.get("valid"): final_score = min(100, final_score + 5)

        # Final decision logic
        threshold = kwargs.get("trust_threshold", 80.0)
        has_hard_flag = any(f.get("type") == "hard" for f in flags)
        layers_covered = sum(1 for ls in layer_scores.values() if ls["is_satisfied"])
        missing_names = [defn["name"] for lid, defn in LAYER_DEFINITIONS.items() if not layer_scores[lid]["is_satisfied"]]
        
        decision = "rejected"
        if final_score >= threshold and not blockers and not has_hard_flag:
            decision = "approved"
        elif not blockers and final_score >= (threshold - 15):
            decision = "review"
        
        result = ToolResult(
            tool_name="scoring_logic",
            output={
                "score": round(final_score, 1),
                "layer_scores": layer_scores,
                "blockers": blockers,
                "flags": flags,
                "documents_coverage": {
                    "total_submitted": len(documents_submitted),
                    "layers_covered": layers_covered,
                    "layers_total": 6,
                    "missing_layers": missing_names
                },
                "decision": decision,
                "threshold_used": threshold
            },
            confidence=final_score / 100.0,
            processing_time_ms=0.0,
        )
        context.results[self.name] = result
        return result
