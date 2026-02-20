from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Literal
from ..services.automedication import evaluate_risk
from ..core.schemas import EvaluationResponse

from backend.core.limiter import limiter

router = APIRouter(prefix="/api/automedication", tags=["automedication"])

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
    result = evaluate_risk(
        answers=body.answers,
        identifier=body.cis,
        has_other_meds=body.has_other_meds or False,
        lang=lang
    )

    from backend.services.search import get_drug_details
    drug_name = "ce médicament" if lang == "fr" else "este medicamento"
    substance_names = []
    is_otc = True
    if body.cis:
        drug_info = get_drug_details(body.cis)
        if drug_info:
            drug_name = drug_info.name
            is_otc = drug_info.is_otc
            substance_names = [bs.substance.name for bs in drug_info.composition]

    result.general_advice = []
        
    if not is_otc:
        warning_msg = "⚠️ Ce médicament nécessite normalement une prescription médicale."
        if warning_msg not in result.details:
            result.details.insert(0, warning_msg)

    from backend.services.automedication.db_repository import AutomedicationRepository
    _repo = AutomedicationRepository()
    if body.cis:
        rules = _repo.get_rules_for_brand(body.cis)
        result.has_coverage = len(rules) > 0
    else:
        result.has_coverage = False

    if result.score != "GREEN":
        from ..services.ai_service import generate_risk_explanation
        
        explanation = await generate_risk_explanation(
            drug_name=drug_name,
            score=result.score,
            details=result.details,
            user_profile={
                "gender": body.gender,
                "age": body.age,
                "has_other_meds": body.has_other_meds,
                "substances": substance_names
            },
            answered_questions=result.answered_questions_context or [],
            lang=lang
        )
        result.ai_explanation = explanation

    return result
