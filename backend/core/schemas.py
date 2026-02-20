from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .models import RiskLevel

class SearchResult(BaseModel):
    type: str         
    id: str           
    name: str
    description: Optional[str] = None

class FlowOption(BaseModel):
    value: str
    label: str

class FlowQuestion(BaseModel):
    id: str
    text: str
    type: str
    options: Optional[List[FlowOption]] = None
    risk_level: Optional[int] = None 
    show_if: Optional[Dict[str, Any]] = None 
    is_profile: bool = False 

class EvaluationResponse(BaseModel):
    score: str 
    details: List[str]
    ai_explanation: Optional[str] = None 
    general_advice: List[str] = [] 
    has_coverage: bool = True 
    answered_questions_context: Optional[List[dict]] = None

    model_config = {
        "json_schema_extra": {"exclude": ["answered_questions_context"]}
    }

    def model_dump(self, **kwargs):
        kwargs.setdefault("exclude", set())
        kwargs["exclude"] = set(kwargs["exclude"]) | {"answered_questions_context"}
        return super().model_dump(**kwargs)
