from typing import List, Dict
import logging
from backend.core.models import Rule, RiskLevel
from backend.core.schemas import EvaluationResponse
from .risk_calculator import RiskCalculator
from .db_repository import AutomedicationRepository

logger = logging.getLogger(__name__)

_repository = AutomedicationRepository()

from backend.core.i18n import i18n

def evaluate_risk(
    answers: Dict[str, bool], 
    identifier: str = None, 
    has_other_meds: bool = False,
    lang: str = "fr"
) -> EvaluationResponse:
    try:
        if not identifier:
            return EvaluationResponse(
                score=RiskLevel.LEVEL_1, 
                details=[],
                answered_questions_context=[]
            )
            
        rules = _repository.get_rules_for_brand(identifier)
        
        if has_other_meds:
            for r in rules:
                if r.filter_polymedication or r.question_code == 'Q_POLYMEDICATION':
                    answers[r.question_code] = True
        
        result = RiskCalculator.compute_score(rules, answers)
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur evaluate_risk: {e}", exc_info=True)
        return EvaluationResponse(
            score=RiskLevel.LEVEL_4, 
            details=[i18n.get('error_analysis', lang, 'risks') or "Erreur technique lors de l'analyse"],
            answered_questions_context=[]
        )

