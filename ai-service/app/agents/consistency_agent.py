import logging
import re
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.tools.name_matcher import NameMatcher
from app.services.layer_registry import DOC_TYPE_TO_LAYER

logger = logging.getLogger(__name__)

NIN_RE = re.compile(r"^(\d{2})(\d{2})(\d{2})\d+$")


def _extract_dob_from_nin(nin: str) -> Optional[date]:
    m = NIN_RE.match(nin)
    if not m:
        return None
    yy, mm, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
    year = 1900 + yy if yy >= 30 else 2000 + yy
    try:
        return date(year, mm, dd)
    except ValueError:
        return None


def _parse_year(val: Any) -> Optional[int]:
    try:
        return int(str(val)[:4])
    except (TypeError, ValueError):
        return None


def _parse_date(val: Any) -> Optional[date]:
    if not val:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(str(val), fmt).date()
        except ValueError:
            continue
    return None


def _extract_field_value(fields: Dict, key: str) -> Optional[str]:
    raw = fields.get(key)
    if isinstance(raw, dict):
        return raw.get("value")
    return raw


def _extract_any_field(fields: Dict, keys: Tuple[str, ...]) -> Optional[str]:
    for k in keys:
        v = _extract_field_value(fields, k)
        if v:
            return str(v)
    return None


class ConsistencyAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "consistency"

    @property
    def tools(self) -> List[BaseTool]:
        return []

    async def run(self, context: AgentContext, **kwargs) -> ToolResult:
        documents: Dict[str, Dict] = kwargs.get("documents", {})
        if not documents and context.get_result("extraction"):
            extraction = context.get_result("extraction")
            documents = extraction.output.get("extracted_fields", {}) if extraction.output else {}

        checks: List[Dict] = []
        flags: List[Dict] = []
        scores: List[float] = []

        # 1. Name consistency
        all_names = []
        for doc_type, fields in documents.items():
            for key in ("name", "full_name", "name_fr", "name_ar", "prenom", "nom", "doctor_name", "owner_name"):
                val = _extract_any_field(fields, (key,))
                if val:
                    all_names.append(str(val))

        name_consistent, name_conf = NameMatcher.compare_all_name_pairs(all_names)
        checks.append({
            "check": "name_consistency",
            "passed": name_consistent,
            "confidence": name_conf,
            "details": f"Compared {len(all_names)} name(s)",
            "values": all_names,
        })
        scores.append(name_conf)
        if name_conf < 0.5:
            flags.append({"type": "hard", "check": "name_consistency", "message": "Name mismatch detected across documents"})
        elif name_conf < 0.75:
            flags.append({"type": "soft", "check": "name_consistency", "message": "Name inconsistency — manual review recommended"})

        # 2. NIN ↔ DOB match
        nin_val = None
        dob_val = None
        for doc_type, fields in documents.items():
            for key in ("nin", "national_id_number"):
                v = _extract_any_field(fields, (key,))
                if v and not nin_val:
                    nin_val = str(v).replace(" ", "")
            for key in ("date_of_birth", "birth_date", "dob"):
                v = _extract_any_field(fields, (key,))
                if v and not dob_val:
                    dob_val = v

        nin_check = {"check": "nin_dob_match", "passed": True, "confidence": 1.0, "details": "NIN not present — skipped"}
        if nin_val and dob_val:
            nin_dob = _extract_dob_from_nin(nin_val)
            doc_dob = _parse_date(dob_val)
            if nin_dob and doc_dob:
                matched = nin_dob == doc_dob
                nin_check = {
                    "check": "nin_dob_match", "passed": matched,
                    "confidence": 1.0 if matched else 0.0,
                    "details": f"NIN DOB={nin_dob} vs Doc DOB={doc_dob}",
                }
                scores.append(1.0 if matched else 0.0)
                if not matched:
                    flags.append({"type": "hard", "check": "nin_dob_match", "message": "NIN date-of-birth mismatch"})
        checks.append(nin_check)

        # 3. Specialty consistency
        specialties = []
        for doc_type, fields in documents.items():
            v = _extract_any_field(fields, ("specialty",))
            if v:
                specialties.append(str(v))

        if len(specialties) >= 2:
            spec_consistent, spec_conf = NameMatcher.compare_all_name_pairs(specialties)
            checks.append({
                "check": "specialty_consistency",
                "passed": spec_consistent,
                "confidence": spec_conf,
                "details": f"Compared {len(specialties)} specialties",
            })
            scores.append(spec_conf)
            if spec_conf < 0.6:
                flags.append({"type": "soft", "check": "specialty_consistency", "message": "Medical specialty mismatch across documents"})
        else:
            checks.append({"check": "specialty_consistency", "passed": True, "confidence": 1.0, "details": "Not enough data"})

        # 4. Ordre Registration Number
        ordre_nums = []
        for doc_type, fields in documents.items():
            v = _extract_any_field(fields, ("ordre_registration_number",))
            if v:
                ordre_nums.append(str(v).strip())

        if len(ordre_nums) >= 2:
            matched = len(set(ordre_nums)) == 1
            checks.append({
                "check": "ordre_number_consistency",
                "passed": matched,
                "confidence": 1.0 if matched else 0.0,
                "details": f"Unique numbers: {list(set(ordre_nums))}",
            })
            scores.append(1.0 if matched else 0.0)
            if not matched:
                flags.append({"type": "hard", "check": "ordre_number_consistency", "message": "Ordre registration number mismatch"})
        else:
            checks.append({"check": "ordre_number_consistency", "passed": True, "confidence": 1.0, "details": "Not enough data"})

        # Aggregate
        overall_score = sum(scores) / len(scores) if scores else 1.0
        overall_consistent = overall_score >= 0.7 and not any(f["type"] == "hard" for f in flags)

        result = ToolResult(
            tool_name="consistency_checks",
            output={
                "overall_consistent": overall_consistent,
                "consistency_score": round(overall_score * 100, 1),
                "checks": checks,
                "flags": flags,
            },
            confidence=overall_score,
            processing_time_ms=0.0,
        )
        context.results[self.name] = result
        return result
