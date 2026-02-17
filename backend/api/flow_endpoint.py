from fastapi import APIRouter, Request
from typing import List, Optional, Dict, Any
from backend.core.limiter import limiter

from backend.core.schemas import FlowQuestion, FlowOption
from ..services.automedication.db_repository import AutomedicationRepository
from ..services.automedication.question_filters import QuestionFilterService

router = APIRouter(prefix="/api/automedication", tags=["automedication-flow"])

_repository = AutomedicationRepository()



def _build_profile_questions(has_gender_questions: bool, has_age_questions: bool) -> List[FlowQuestion]:
    profile = []
    
    if has_gender_questions:
        profile.append(FlowQuestion(
            id="GENDER",
            text="Quel est votre sexe ?",
            type="choice",
            options=[
                FlowOption(value="M", label="Un homme"),
                FlowOption(value="F", label="Une femme")
            ],
            is_profile=True
        ))
    
    if has_age_questions:
        profile.append(FlowQuestion(
            id="AGE",
            text="Quel âge avez-vous ?",
            type="number",
            is_profile=True
        ))
    
    profile.append(FlowQuestion(
        id="HAS_OTHER_MEDS",
        text="Prenez-vous d'autres médicaments au quotidien ?",
        type="boolean",
        is_profile=True
    ))
    
    return profile


def _convert_medical_questions(questions, route: str = None) -> List[FlowQuestion]:
    if route:
        questions = QuestionFilterService.filter_by_route(questions, route)
    
    flow_questions = []
    for q in questions:
        if q.id.startswith("Q_POLYMEDICATION"):
            continue
        
        show_if = {}
        
        if q.target_gender:
            show_if["GENDER"] = q.target_gender
        
        if q.age_min is not None:
            show_if["AGE_MIN"] = q.age_min
        
        if q.age_max is not None:
            show_if["AGE_MAX"] = q.age_max
        
        if q.requires_other_meds:
            show_if["HAS_OTHER_MEDS"] = True
        
        flow_questions.append(FlowQuestion(
            id=q.id,
            text=q.text,
            type="boolean",
            risk_level=q.risk_level.value,
            show_if=show_if if show_if else None,
            is_profile=False
        ))
    
    return flow_questions


@router.get("/flow/{identifier}", response_model=List[FlowQuestion])
@limiter.limit("30/minute")

async def get_flow(request: Request, identifier: str):
    tags = _repository.get_substance_tags(identifier)
    
    if not tags:
        return []
    
    all_medical_questions = _repository.get_questions_by_tags(tags)
    
    route = _repository.get_drug_route(identifier)
    
    medical_flow = _convert_medical_questions(all_medical_questions, route)
    
    has_gender_questions = any(q.target_gender is not None for q in all_medical_questions)
    has_age_questions = any(
        q.age_min is not None or q.age_max is not None 
        for q in all_medical_questions
    )
    
    profile_flow = _build_profile_questions(has_gender_questions, has_age_questions)
    
    return profile_flow + medical_flow
