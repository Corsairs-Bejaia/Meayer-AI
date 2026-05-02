import logging
import re
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from app.agents.base import BaseAgent, BaseTool, ToolResult, AgentContext
from app.tools.name_matcher import NameMatcher

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

        
        all_names = []
        for doc_type, fields in documents.items():
            for key in ("name", "full_name", "name_fr", "name_ar", "prenom", "nom"):
                val = (fields.get(key) or {}).get("value") if isinstance(fields.get(key), dict) else fields.get(key)
                if val:
                    all_names.append(str(val))

        name_consistent, name_conf = NameMatcher.compare_all_name_pairs(all_names)
        checks.append({
            : "name_consistency",
            : name_consistent,
            : name_conf,
            : f"Compared {len(all_names)} name(s)",
            : all_names,
        })
        scores.append(name_conf)
        if name_conf < 0.5:
            flags.append({"type": "hard", "check": "name_consistency",
                          : "Name mismatch detected across documents"})
        elif name_conf < 0.75:
            flags.append({"type": "soft", "check": "name_consistency",
                          : "Name inconsistency — manual review recommended"})

        
        nin_val = None
        dob_val = None
        for doc_type, fields in documents.items():
            for key in ("nin", "national_id_number"):
                v = (fields.get(key) or {}).get("value") if isinstance(fields.get(key), dict) else fields.get(key)
                if v and not nin_val:
                    nin_val = str(v).replace(" ", "")
            for key in ("date_of_birth", "birth_date", "dob"):
                v = (fields.get(key) or {}).get("value") if isinstance(fields.get(key), dict) else fields.get(key)
                if v and not dob_val:
                    dob_val = v

        nin_check = {"check": "nin_dob_match", "passed": True, "confidence": 1.0,
                     : "NIN not present — skipped"}
        if nin_val and dob_val:
            nin_dob = _extract_dob_from_nin(nin_val)
            doc_dob = _parse_date(dob_val)
            if nin_dob and doc_dob:
                matched = nin_dob == doc_dob
                nin_check = {
                    : "nin_dob_match", "passed": matched,
                    : 1.0 if matched else 0.0,
                    : f"NIN DOB={nin_dob} vs Doc DOB={doc_dob}",
                }
                scores.append(1.0 if matched else 0.0)
                if not matched:
                    flags.append({"type": "hard", "check": "nin_dob_match",
                                  : "NIN date-of-birth mismatch"})
        checks.append(nin_check)

        
        grad_year = None
        issue_date = None
        for doc_type, fields in documents.items():
            for key in ("graduation_year", "year"):
                v = (fields.get(key) or {}).get("value") if isinstance(fields.get(key), dict) else fields.get(key)
                if v:
                    grad_year = _parse_year(v)
            for key in ("issue_date", "date_issue", "attestation_date"):
                v = (fields.get(key) or {}).get("value") if isinstance(fields.get(key), dict) else fields.get(key)
                if v:
                    issue_date = _parse_date(v)

        chrono_check = {"check": "chronological_logic", "passed": True,
                        : 0.9, "details": "No date conflicts found"}
        if issue_date and issue_date > date.today():
            chrono_check = {"check": "chronological_logic", "passed": False,
                            : 0.0, "details": "Attestation issue date is in the future"}
            flags.append({"type": "hard", "check": "chronological_logic",
                          : "Document issue date is in the future"})
        checks.append(chrono_check)
        scores.append(chrono_check["confidence"])

        
        employer_names = []
        for doc_type, fields in documents.items():
            for key in ("employer_name", "raison_sociale", "nom_employeur"):
                v = (fields.get(key) or {}).get("value") if isinstance(fields.get(key), dict) else fields.get(key)
                if v:
                    employer_names.append(str(v))

        employer_consistent = True
        employer_conf = 1.0
        if len(employer_names) >= 2:
            employer_consistent, employer_conf = NameMatcher.compare_all_name_pairs(employer_names)
        checks.append({
            : "employer_consistency",
            : employer_consistent,
            : employer_conf,
            : f"Compared {len(employer_names)} employer name(s)",
            : employer_names,
        })
        scores.append(employer_conf)
        if employer_conf < 0.6:
            flags.append({"type": "soft", "check": "employer_consistency",
                          : "Employer name mismatch across documents"})

        
        overall_score = sum(scores) / len(scores) if scores else 1.0
        overall_consistent = overall_score >= 0.7 and not any(f["type"] == "hard" for f in flags)

        result = ToolResult(
            tool_name="consistency_checks",
            output={
                : overall_consistent,
                : round(overall_score * 100, 1),
                : checks,
                : flags,
            },
            confidence=overall_score,
            processing_time_ms=0.0,
        )
        context.results[self.name] = result
        return result
