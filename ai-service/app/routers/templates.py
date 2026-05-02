from fastapi import APIRouter, Depends
from typing import List
from app.services.template_service import TemplateService
from app.schemas.schemas import Template
from app.dependencies import verify_api_key

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("", response_model=List[Template])
async def list_templates(_: str = Depends(verify_api_key)):
    """Returns all predefined document templates."""
    return TemplateService.list_all()

@router.get("/{slug}", response_model=Template)
async def get_template(slug: str, _: str = Depends(verify_api_key)):
    """Returns a specific template by its slug."""
    tpl = TemplateService.get_template(slug)
    if not tpl:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl
