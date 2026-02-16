"""
Endpoint unifié pour le flux d'automédication.
Retourne toutes les questions (profil + médicales) en un seul appel,
ordonnées et avec des conditions d'affichage (showIf).
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from ..services.automedication.db_repository import AutomedicationRepository
from ..services.automedication.question_filters import QuestionFilterService

router = APIRouter(prefix="/api/automedication", tags=["automedication-flow"])

# --- Schemas de réponse ---

class FlowOption(BaseModel):
    """Option pour une question de type 'choice'"""
    value: str
    label: str

class FlowQuestion(BaseModel):
    """Question unifiée pour le flux frontend"""
    id: str
    text: str
    type: str  # "choice" | "number" | "boolean"
    options: Optional[List[FlowOption]] = None
    risk_level: Optional[str] = None  # Uniquement pour les questions médicales
    show_if: Optional[Dict[str, Any]] = None  # Condition d'affichage
    is_profile: bool = False  # True si c'est une question de profil (pas médicale)

# --- Instance partagée ---
_repository = AutomedicationRepository()


def _build_profile_questions(has_gender_questions: bool, has_age_questions: bool) -> List[FlowQuestion]:
    """
    Construit les questions de profil nécessaires selon le médicament.
    On ne pose genre/âge que si des questions médicales en dépendent.
    """
    profile = []
    
    # Le sexe n'est posé que s'il y a des questions genrées (ex: grossesse)
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
    
    # L'âge n'est posé que s'il y a des questions avec filtre d'âge
    if has_age_questions:
        profile.append(FlowQuestion(
            id="AGE",
            text="Quel âge avez-vous ?",
            type="number",
            is_profile=True
        ))
    
    # Autres médicaments : toujours posé (impacte la polymédication)
    profile.append(FlowQuestion(
        id="HAS_OTHER_MEDS",
        text="Prenez-vous d'autres médicaments au quotidien ?",
        type="boolean",
        is_profile=True
    ))
    
    return profile


def _convert_medical_questions(questions, route: str = None) -> List[FlowQuestion]:
    """
    Convertit les questions DB en FlowQuestion, 
    sans appliquer les filtres genre/âge/polymeds (ils seront gérés côté front via showIf).
    On applique seulement le filtre de route d'administration (invariant).
    """
    # Filtre par route uniquement (c'est lié au médicament, pas au patient)
    if route:
        questions = QuestionFilterService.filter_by_route(questions, route)
    
    flow_questions = []
    for q in questions:
        # Exclure les questions de polymédication (déjà collectée via HAS_OTHER_MEDS dans le profil)
        if q.id.startswith("Q_POLYMEDICATION"):
            continue
        
        # Construire les conditions showIf
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
async def get_flow(identifier: str):
    """
    Retourne le flux complet de questions pour un médicament/substance.
    Combine questions de profil (genre, âge, polymédication) et questions
    médicales spécifiques, ordonnées pour une présentation une-par-une.
    
    Le frontend gère le 'showIf' côté client pour skipper les questions
    non pertinentes selon les réponses précédentes.
    """
    # 1. Récupérer les tags du médicament/substance
    tags = _repository.get_substance_tags(identifier)
    
    if not tags:
        # Aucun tag = aucune question connue = résultat vert direct
        return []
    
    # 2. Récupérer toutes les questions médicales brutes (sans filtrage patient)
    all_medical_questions = _repository.get_questions_by_tags(tags)
    
    # 3. Récupérer la route d'administration
    route = _repository.get_drug_route(identifier)
    
    # 4. Convertir les questions médicales (avec filtre route uniquement)
    medical_flow = _convert_medical_questions(all_medical_questions, route)
    
    # 5. Déterminer quelles questions de profil sont nécessaires (smart skip)
    has_gender_questions = any(q.target_gender is not None for q in all_medical_questions)
    has_age_questions = any(
        q.age_min is not None or q.age_max is not None 
        for q in all_medical_questions
    )
    
    # 6. Construire les questions de profil nécessaires
    profile_flow = _build_profile_questions(has_gender_questions, has_age_questions)
    
    # 7. Retourner le flux complet : profil d'abord, puis médical
    return profile_flow + medical_flow
