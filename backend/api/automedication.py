"""
Endpoints API pour le système de Score d'Automédication (KISS).
Connecté aux services simplifiés et à la base SQLite nettoyée.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from ..services.automedication import get_questions_for_drug, evaluate_risk
from ..core.schemas import EvaluationResponse
from ..core.models import Question

router = APIRouter(prefix="/api/automedication", tags=["automedication"])

class AnswersRequest(BaseModel):
    """Payload pour envoyer les réponses"""
    # Identifier (CIS ou code substance) pour vérifier les risques de polymédication
    cis: Optional[str] = None
    answers: Dict[str, bool]  # {"Q_GROSSESSE": true}
    # Indique si le patient prend d'autres médicaments (pour le risque polymédication automatique)
    has_other_meds: Optional[bool] = False
    gender: Optional[str] = None
    age: Optional[int] = None

@router.get("/questions/{cis}", response_model=List[Question])
async def get_questions(
    cis: str,
    gender: Optional[str] = None,
    age: Optional[int] = None,
    has_other_meds: Optional[bool] = False
):
    """
    Récupère les risques (questions) pour un médicament donné.
    Le service va chercher les substances du médicament -> tags -> questions.
    
    Query Parameters (optionnels):
    - gender: "M" ou "F" - Filtre les questions par genre
    - age: int - Filtre les questions par âge (ex: questions seniors si age>=65)
    - has_other_meds: bool - Affiche les questions de polymédication si True
    """
    questions = get_questions_for_drug(
        identifier=cis,
        patient_gender=gender,
        patient_age=age,
        has_other_meds=has_other_meds
    )
    return questions

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: AnswersRequest):
    """
    Calcule le score final basé sur les réponses OUI (True).
    Si cis et has_other_meds sont fournis, applique automatiquement
    le risque de polymédication (sans reposer la question).
    """
    result = evaluate_risk(
        answers=request.answers,
        identifier=request.cis,
        has_other_meds=request.has_other_meds or False
    )

    # Enrichissement avec IA si Risque (Orange/Rouge)
    if result.score.value != "GREEN":
        from ..services.ai_service import generate_risk_explanation
        from ..services.search_service import get_drug_details
        
        # On récupère le nom du médicament
        drug_name = "ce médicament"
        if request.cis:
            drug_info = get_drug_details(request.cis)
            if drug_info:
                drug_name = drug_info.name
        
        # Appel asynchrone au service IA avec le contexte enrichi
        explanation = await generate_risk_explanation(
            drug_name=drug_name,
            score=result.score.value,
            details=result.details,
            user_profile={
                "gender": request.gender,
                "age": request.age,
                "has_other_meds": request.has_other_meds
            },
            answered_questions=result.answered_questions_context or []
        )
        result.ai_explanation = explanation

    return result

