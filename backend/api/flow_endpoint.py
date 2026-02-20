from fastapi import APIRouter, Request, Query
from typing import List, Optional, Dict, Any
from backend.core.limiter import limiter

from backend.core.schemas import FlowQuestion, FlowOption
from ..services.automedication.db_repository import AutomedicationRepository
from backend.core.i18n import i18n
from backend.core.models import Rule

router = APIRouter(prefix="/api/automedication", tags=["automedication-flow"])

_repository = AutomedicationRepository()


def _build_profile_questions(has_gender_questions: bool, has_age_questions: bool, lang: str = "fr") -> List[FlowQuestion]:
    profile = []
    
    if has_gender_questions:
        profile.append(FlowQuestion(
            id="GENDER",
            text=i18n.get("GENDER", lang, "questions") or "Quel est votre sexe ?",
            type="choice",
            options=[
                FlowOption(value="M", label=i18n.get("gender_male", lang, "options") or "Un homme"),
                FlowOption(value="F", label=i18n.get("gender_female", lang, "options") or "Une femme")
            ],
            is_profile=True
        ))
    
    if has_age_questions:
        profile.append(FlowQuestion(
            id="AGE",
            text=i18n.get("AGE", lang, "questions") or "Quel âge avez-vous ?",
            type="number",
            is_profile=True
        ))
    
    profile.append(FlowQuestion(
        id="HAS_OTHER_MEDS",
        text=i18n.get("HAS_OTHER_MEDS", lang, "questions") or "Prenez-vous d'autres médicaments au quotidien ?",
        type="boolean",
        is_profile=True
    ))
    
    return profile


def _convert_rules_to_questions(rules: List[Rule], route: str = None, lang: str = "fr") -> List[FlowQuestion]:
    flow_questions_dict = {}
    
    for rule in rules:
        if rule.question_code == "GENERAL" or rule.question_code.startswith("Q_POLYMEDICATION") or rule.filter_polymedication:
            continue
            
        if rule.filter_route and route:
            if rule.filter_route.lower() not in route.lower():
                continue

        if rule.question_code not in flow_questions_dict:
            show_if = {}
            
            if rule.filter_gender:
                show_if["GENDER"] = rule.filter_gender
            
            if rule.age_min is not None:
                show_if["AGE_MIN"] = rule.age_min
                
            translated_text = i18n.translate_question(rule.question_code, rule.question_code, lang)
            
            flow_questions_dict[rule.question_code] = FlowQuestion(
                id=rule.question_code,
                text=translated_text,
                type="boolean",
                risk_level=rule.risk_level.value,
                show_if=show_if if show_if else None,
                is_profile=False
            )
        else:
            q = flow_questions_dict[rule.question_code]
            if rule.risk_level.value > q.risk_level:
                q.risk_level = rule.risk_level.value

    return list(flow_questions_dict.values())


@router.get("/flow/{identifier}", response_model=List[FlowQuestion])
@limiter.limit("30/minute")
async def get_flow(request: Request, identifier: str, lang: str = Query("fr")):
    rules = _repository.get_rules_for_brand(identifier)
    
    if not rules:
        return _build_profile_questions(False, False, lang)
        
    for r in rules:
        if r.question_code == "GENERAL" and r.risk_level.value == 4:
            return []
    
    route = _repository.get_drug_route(identifier)
    
    medical_flow = _convert_rules_to_questions(rules, route, lang)
    
    has_gender_questions = any(r.filter_gender is not None for r in rules)
    has_age_questions = any(r.age_min is not None for r in rules)
    
    profile_flow = _build_profile_questions(has_gender_questions, has_age_questions, lang)
    
    return profile_flow + medical_flow
