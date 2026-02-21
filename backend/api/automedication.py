from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Optional, Literal
from backend.core.schemas import EvaluationResponse
from backend.core.limiter import limiter
from backend.services.automedication.orchestrator import AutomedicationOrchestrator

router = APIRouter(prefix="/api/automedication", tags=["automedication"])

_orchestrator = AutomedicationOrchestrator()


class AnswersRequest(BaseModel):
    cis: Optional[str] = Field(None, max_length=50)
    answers: Dict[str, bool] = Field(default_factory=dict)
    has_other_meds: Optional[bool] = False
    gender: Optional[Literal["M", "F"]] = None
    age: Optional[int] = Field(None, ge=0, le=150)

    @field_validator('answers')
    @classmethod
    def limit_answers_size(cls, v):
        if len(v) > 50:
            raise ValueError("Trop de réponses envoyées (max 50)")
        return v


@router.post("/evaluate", response_model=EvaluationResponse)
@limiter.limit("10/minute")
async def evaluate(request: Request, body: AnswersRequest, lang: str = "fr"):
    """Évalue le risque d'automédication pour un médicament donné."""
    return await _orchestrator.evaluate(
        cis=body.cis,
        answers=body.answers,
        has_other_meds=body.has_other_meds or False,
        gender=body.gender,
        age=body.age,
        lang=lang
    )
