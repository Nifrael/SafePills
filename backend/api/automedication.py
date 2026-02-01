"""
Endpoints API pour le système de Score d'Automédication (KISS).
Connecté aux services simplifiés et à la base SQLite nettoyée.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from ..services.automedication_service import get_questions_for_drug, evaluate_risk
from ..core.schemas import EvaluationResponse
from ..core.models import Question

router = APIRouter(prefix="/api/automedication", tags=["automedication"])

class AnswersRequest(BaseModel):
    """Payload pour envoyer les réponses"""
    # On n'a même pas forcément besoin du CIS ici, juste des réponses
    # Mais on le garde pour du logging éventuel
    cis: Optional[str] = None
    answers: Dict[str, bool]  # {"Q_GROSSESSE": true}

@router.get("/questions/{cis}", response_model=List[Question])
async def get_questions(cis: str):
    """
    Récupère les risques (questions) pour un médicament donné.
    Le service va chercher les substances du médicament -> tags -> questions.
    """
    questions = get_questions_for_drug(cis)
    # On renvoie une liste vide si pas de risque, c'est valide
    return questions

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: AnswersRequest):
    """
    Calcule le score final basé sur les réponses OUI (True).
    """
    result = evaluate_risk(request.answers)
    return result
