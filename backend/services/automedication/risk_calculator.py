from typing import Dict, List
from backend.core.models import Rule, RiskLevel
from backend.core.schemas import EvaluationResponse


class RiskCalculator:

    @staticmethod
    def compute_score(rules: List[Rule], answers: Dict[str, bool]) -> EvaluationResponse:

        score = RiskLevel.LEVEL_1
        details = []
        answered_questions_context = []
        
        for rule in rules:
            is_general = rule.question_code == "GENERAL"
            answer = True if is_general else answers.get(rule.question_code, False)
            
            if answer:  
                answered_questions_context.append({
                    'question_id': rule.question_code,
                    'question_text': rule.question_code,
                    'answer': 'OUI',
                    'risk_level': rule.risk_level.value,
                    'triggers_alert': True
                })
                
                if rule.risk_level > score:
                    score = rule.risk_level
                
                if rule.advice:
                    if rule.advice not in details:
                        details.append(rule.advice)
        
        score_str = "GREEN"
        if score == RiskLevel.LEVEL_2:
            score_str = "YELLOW"
        elif score == RiskLevel.LEVEL_3:
            score_str = "ORANGE"
        elif score >= RiskLevel.LEVEL_4:
            score_str = "RED"
            
        return EvaluationResponse(
            score=score_str,
            details=details,
            answered_questions_context=answered_questions_context
        )

