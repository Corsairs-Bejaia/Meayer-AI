import json
import logging
import os
from typing import List, Optional, Dict
from app.schemas.schemas import Template

logger = logging.getLogger(__name__)

class TemplateService:
    _templates: Dict[str, Template] = {}
    _data_path = os.path.join(os.path.dirname(__file__), "..", "data", "templates.json")

    @classmethod
    def load_templates(cls):
        """Loads templates from JSON file into memory."""
        try:
            if not os.path.exists(cls._data_path):
                logger.warning(f"Template file not found at {cls._data_path}")
                return

            with open(cls._data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    tpl = Template(**item)
                    cls._templates[tpl.slug] = tpl
            
            logger.info(f"Loaded {len(cls._templates)} document templates.")
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")

    @classmethod
    def get_template(cls, slug: str) -> Optional[Template]:
        return cls._templates.get(slug)

    @classmethod
    def get_templates_by_type(cls, doc_type: str) -> List[Template]:
        return [t for t in cls._templates.values() if t.doc_type == doc_type]

    @classmethod
    def list_all(cls) -> List[Template]:
        return list(cls._templates.values())

# Initialize on module load
TemplateService.load_templates()
