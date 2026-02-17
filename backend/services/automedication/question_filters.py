from typing import List
from backend.core.models import Question


class QuestionFilterService:
    
    @staticmethod
    def filter_by_route(questions: List[Question], route: str = None) -> List[Question]:
        if not route:
            return questions
            
        filtered = []
        normalized_route = route.lower()
        
        for q in questions:
            if not q.applicable_routes:
                filtered.append(q)
                continue
                
            is_applicable = False
            for allowed in q.applicable_routes:
                if allowed in normalized_route:
                    is_applicable = True
                    break
            
            if is_applicable:
                filtered.append(q)
                
        return filtered
