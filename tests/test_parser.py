import pytest
from app.services.result_parser import parse_cnas_result

def test_parse_valid_result():
    html = """
    <table>
        <tr><td>Raison Sociale</td><td>ALGERIA TECH SPA</td></tr>
        <tr><td>Etat de l'attestation</td><td>Valide</td></tr>
    </table>
    """
    result = parse_cnas_result(html)
    assert result["valid"] is True
    assert result["employer_name"] == "ALGERIA TECH SPA"
    assert result["attestation_status"] == "Valide"

def test_parse_not_found():
    html = "<div>aucune attestation trouvée</div>"
    result = parse_cnas_result(html)
    assert result["valid"] is False
    assert result["status"] == "not_found"

def test_parse_captcha_failed():
    html = "<div>Captcha Incorrect</div>"
    result = parse_cnas_result(html)
    assert result["status"] == "captcha_failed"

def test_parse_employee_found():
    html = """
    <table>
        <tr><td>Raison Sociale</td><td>ALGERIA TECH SPA</td></tr>
        <tr><td>850101123456</td><td>Younes B.</td></tr>
    </table>
    """
    result = parse_cnas_result(html, ssn_to_find="850101123456")
    assert result["employee_found"] is True
    assert result["employee_name"] == "Younes B."
