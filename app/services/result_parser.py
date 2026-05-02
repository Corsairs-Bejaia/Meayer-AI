import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def parse_cnas_result(html_content: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html_content, 'lxml')
    
    result = {
        "valid": False,
        "status": "not_found",
        "employer_name": None,
        "attestation_status": None,
        "error_message": None
    }

    if "Captcha Incorrect" in html_content or "Code de sécurité incorrect" in html_content:
        result["status"] = "captcha_failed"
        return result

    if "aucune attestation" in html_content.lower() or "n'est pas valide" in html_content.lower():
        result["valid"] = False
        result["status"] = "not_found"
        return result

    try:
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                text = row.get_text().strip()
                if "Raison Sociale" in text or "Employeur" in text:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        result["employer_name"] = cells[1].get_text().strip()
                        result["valid"] = True
                        result["status"] = "verified"
                
                if "Etat de l'attestation" in text or "Statut" in text:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        result["attestation_status"] = cells[1].get_text().strip()
    except Exception as e:
        logger.error(f"Error parsing CNAS HTML: {e}")
        result["status"] = "parse_error"

    if result["employer_name"]:
        result["valid"] = True
        result["status"] = "verified"

    return result
