"""
Calculateur de risque d'automédication.
Logique métier pure (sans accès base de données).
"""
from typing import Dict, List
from backend.core.models import Question, RiskLevel
from backend.core.schemas import EvaluationResponse


class RiskCalculator:

    @staticmethod
    def compute_score(questions: List[Question], answers: Dict[str, bool]) -> EvaluationResponse:

        score = RiskLevel.GREEN
        details = []
        answered_questions_context = []
        
        for q in questions:
            answer = answers.get(q.id, False)
            
            if answer:  
                answered_questions_context.append({
                    'question_id': q.id,
                    'question_text': q.text,
                    'answer': 'OUI',
                    'risk_level': q.risk_level.value,
                    'triggers_alert': True
                })
                
                if q.risk_level == RiskLevel.RED:
                    score = RiskLevel.RED
                    details.append(f"ALERTE ROUGE : {q.text} (Contre-indication formelle)")
                    break
                    
                elif q.risk_level == RiskLevel.ORANGE and score != RiskLevel.RED:
                    score = RiskLevel.ORANGE
                    details.append(f"Attention : {q.text} (Précautions nécessaires)")
        
        return EvaluationResponse(
            score=score,
            details=details,
            answered_questions_context=answered_questions_context
        )
    
    @staticmethod
    def get_polymeds_risk_from_tags(tags: List[str]) -> RiskLevel | None:

        if not tags:
            return None
        
        has_red = False
        has_orange = False
        
        for tag in tags:
            tag_upper = tag.upper()
            if "POLYMEDICAMENTATION_RED" in tag_upper or "POLYMEDS_RED" in tag_upper:
                has_red = True
            elif "POLYMEDICAMENTATION_ORANGE" in tag_upper or "POLYMEDS_ORANGE" in tag_upper:
                has_orange = True
        
        if has_red:
            return RiskLevel.RED
        elif has_orange:
            return RiskLevel.ORANGE
        else:
            return None
    
    @staticmethod
    def build_ai_context(questions: List[Question], answers: Dict[str, bool]) -> List[dict]:

        context = []
        
        for q in questions:
            answer = answers.get(q.id, False)
            if answer:  
                context.append({
                    'question_text': q.text,
                    'answer': 'OUI',
                    'risk_level': q.risk_level.value,
                    'triggers_alert': True
                })
        
        return context
