"""
Endpoints API pour le système de Score d'Automédication (KISS).
Connecté aux services simplifiés et à la base SQLite nettoyée.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Literal
from ..services.automedication import get_questions_for_drug, evaluate_risk
from ..core.schemas import EvaluationResponse
from ..core.models import Question

router = APIRouter(prefix="/api/automedication", tags=["automedication"])

class AnswersRequest(BaseModel):
    """Payload pour envoyer les réponses — avec des garde-fous !"""
    # CIS : on accepte max 50 caractères, que des lettres/chiffres/accents/espaces
    cis: Optional[str] = Field(None, max_length=50)
    # Réponses : max 50 entrées (on n'a jamais autant de questions)
    answers: Dict[str, bool] = Field(default_factory=dict)
    has_other_meds: Optional[bool] = False
    # Genre : uniquement "M" ou "F", rien d'autre
    gender: Optional[Literal["M", "F"]] = None
    # Âge : entre 0 et 150 ans (personne ne vit plus longtemps !)
    age: Optional[int] = Field(None, ge=0, le=150)

    @field_validator('answers')
    @classmethod
    def limit_answers_size(cls, v):
        """Empêche d'envoyer un dictionnaire géant pour surcharger le serveur"""
        if len(v) > 50:
            raise ValueError("Trop de réponses envoyées (max 50)")
        return v

@router.get("/questions/{cis}", response_model=List[Question])
async def get_questions(
    request: Request,
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

# Limite stricte : 10/minute — C'est l'endpoint LE PLUS cher
# car il appelle Google Gemini (IA payante) quand le score n'est pas GREEN
@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: Request, body: AnswersRequest):
    """
    Calcule le score final basé sur les réponses OUI (True).
    Si cis et has_other_meds sont fournis, applique automatiquement
    le risque de polymédication (sans reposer la question).
    """
    result = evaluate_risk(
        answers=body.answers,
        identifier=body.cis,
        has_other_meds=body.has_other_meds or False
    )

    # Récupérer les infos du médicament (substances)
    from ..services.search_service import get_drug_details
    drug_name = "ce médicament"
    substance_names = []
    if body.cis:
        drug_info = get_drug_details(body.cis)
        if drug_info:
            drug_name = drug_info.name
            substance_names = [s.name for s in drug_info.substances]

    # --- P1-A : Conseils généraux (pour TOUS les scores, y compris GREEN) ---
    # On lit les conseils "general" depuis medical_knowledge.json
    import json, os
    knowledge_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'medical_knowledge.json'
    )
    try:
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            knowledge = json.load(f)
        substance_advice = knowledge.get('substance_advice', {})
        general_tips = []
        for sub in substance_names:
            for tip in substance_advice.get(sub, {}).get('general', []):
                if tip not in general_tips:
                    general_tips.append(tip)
        result.general_advice = general_tips
    except Exception:
        result.general_advice = []

    # --- P1-B : Indicateur de couverture ---
    # Si le patient n'a répondu à aucune question médicale, c'est un faux GREEN
    has_medical_questions = any(
        not q_id.startswith(('GENDER', 'AGE', 'HAS_OTHER'))
        for q_id in body.answers.keys()
    )
    result.has_coverage = has_medical_questions

    # Enrichissement avec IA si Risque (Orange/Rouge)
    if result.score.value != "GREEN":
        from ..services.ai_service import generate_risk_explanation
        
        explanation = await generate_risk_explanation(
            drug_name=drug_name,
            score=result.score.value,
            details=result.details,
            user_profile={
                "gender": body.gender,
                "age": body.age,
                "has_other_meds": body.has_other_meds,
                "substances": substance_names
            },
            answered_questions=result.answered_questions_context or []
        )
        result.ai_explanation = explanation

    return result
