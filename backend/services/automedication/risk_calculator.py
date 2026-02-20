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
        
        return EvaluationResponse(
            score=score,
            details=details,
            answered_questions_context=answered_questions_context
        )
    
    @staticmethod
    def build_ai_context(rules: List[Rule], answers: Dict[str, bool]) -> List[dict]:

        context = []
        
        for rule in rules:
            is_general = rule.question_code == "GENERAL"
            answer = True if is_general else answers.get(rule.question_code, False)
            if answer:  
                context.append({
                    'question_text': rule.question_code,
                    'answer': 'OUI',
                    'risk_level': rule.risk_level.value,
                    'triggers_alert': True
                })
        
        return context

