"""
Module d'automédication refactoré.
Architecture en couches avec séparation des responsabilités.

API publique compatible avec l'ancien automedication_service.py
"""
from typing import List, Dict
import logging
from backend.core.models import Question, RiskLevel
from backend.core.schemas import EvaluationResponse
from .question_filters import QuestionFilterService
from .risk_calculator import RiskCalculator
from .db_repository import AutomedicationRepository

logger = logging.getLogger(__name__)


# Instance partagée du repository
_repository = AutomedicationRepository()


def get_questions_for_drug(
    identifier: str, 
    patient_gender: str = None,
    patient_age: int = None,
    has_other_meds: bool = False
) -> List[Question]:
    """
    Récupère les questions pertinentes pour un médicament/substance.
    
    Args:
        identifier: CIS (médicament) ou Code Substance
        patient_gender: 'M', 'F' ou None
        patient_age: Âge du patient ou None
        has_other_meds: Le patient prend-il d'autres médicaments ?
        
    Returns:
        Liste des questions filtrées et pertinentes
    """
    # 1. Récupérer les tags de la substance/médicament
    tags = _repository.get_substance_tags(identifier)
    
    if not tags:
        logger.debug(f"Aucun tag trouvé pour {identifier}")
        return []
    
    logger.debug(f"Tags trouvés pour {identifier}: {tags}")
    
    # 2. Récupérer toutes les questions correspondant aux tags
    all_questions = _repository.get_questions_by_tags(tags)
    
    if not all_questions:
        logger.debug(f"Aucune question trouvée pour les tags {tags}")
        return []
    
    logger.debug(f"{len(all_questions)} questions trouvées avant filtrage")
    
    # 3. Récupérer la route d'administration si c'est un médicament
    route = _repository.get_drug_route(identifier)
    
    # 4. Appliquer tous les filtres
    filtered_questions = QuestionFilterService.apply_all_filters(
        all_questions,
        route=route,
        gender=patient_gender,
        age=patient_age,
        has_other_meds=has_other_meds
    )
    
    logger.debug(f"{len(filtered_questions)} questions après filtrage")
    
    return filtered_questions


def evaluate_risk(
    answers: Dict[str, bool], 
    identifier: str = None, 
    has_other_meds: bool = False
) -> EvaluationResponse:
    """
    Évalue le risque d'automédication basé sur les réponses du patient.
    
    Args:
        answers: Dictionnaire {question_id: bool}
        identifier: Identifiant du médicament/substance (optionnel)
        has_other_meds: Le patient prend-il d'autres médicaments ?
        
    Returns:
        EvaluationResponse avec score, details et contexte pour l'IA
    """
    try:
        # 1. Récupérer les questions complètes depuis la DB
        answered_ids = list(answers.keys())
        questions = _repository.get_questions_by_ids(answered_ids)
        
        # 2. Calculer le score de risque
        result = RiskCalculator.compute_score(questions, answers)
        
        # 3. Vérifier le risque de polymédication si applicable
        if identifier and has_other_meds:
            tags = _repository.get_substance_tags(identifier)
            polymeds_risk = RiskCalculator.get_polymeds_risk_from_tags(tags)
            
            if polymeds_risk:
                # Ajouter le contexte polymédication pour l'IA
                polymeds_context = {
                    'question_text': 'Prenez-vous d\'autres médicaments de façon régulière ?',
                    'answer': 'OUI',
                    'risk_level': polymeds_risk.value,
                    'triggers_alert': True
                }
                
                if polymeds_risk == RiskLevel.RED:
                    result.score = RiskLevel.RED
                    result.details.append(
                        "ALERTE ROUGE : Vous prenez d'autres médicaments de façon régulière (Risque d'interactions)"
                    )
                    result.answered_questions_context.append(polymeds_context)
                    
                elif polymeds_risk == RiskLevel.ORANGE and result.score != RiskLevel.RED:
                    result.score = RiskLevel.ORANGE
                    result.details.append(
                        "Attention : Vous prenez d'autres médicaments de façon régulière (Précautions requises)"
                    )
                    result.answered_questions_context.append(polymeds_context)
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur evaluate_risk: {e}", exc_info=True)
        return EvaluationResponse(
            score=RiskLevel.RED, 
            details=["Erreur technique lors de l'analyse"],
            answered_questions_context=[]
        )


def get_polymedicamentation_risk(identifier: str) -> RiskLevel | None:
    """
    Récupère le niveau de risque de polymédication pour une substance/médicament.
    
    Args:
        identifier: CIS ou Code Substance
        
    Returns:
        RiskLevel.RED, RiskLevel.ORANGE ou None
    """
    tags = _repository.get_substance_tags(identifier)
    return RiskCalculator.get_polymeds_risk_from_tags(tags)


# Ré-exporter les fonctions de filtrage pour compatibilité avec les tests
filter_questions_by_route = QuestionFilterService.filter_by_route
filter_questions_by_gender = QuestionFilterService.filter_by_gender
filter_questions_by_age = QuestionFilterService.filter_by_age
filter_questions_by_polymedicamentation = QuestionFilterService.filter_by_polymedicamentation
compute_risk_score = RiskCalculator.compute_score
