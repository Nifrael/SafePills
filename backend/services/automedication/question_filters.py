"""
Filtres pour les questions d'automédication.
Logique métier pure (sans accès base de données).
"""
from typing import List
from backend.core.models import Question


class QuestionFilterService:
    """Service de filtrage des questions selon le contexte patient"""
    
    @staticmethod
    def filter_by_route(questions: List[Question], route: str = None) -> List[Question]:
        """
        Filtre les questions qui ne s'appliquent pas à la voie d'administration donnée.
        Si route est None (ex: recherche substance), on garde tout par prudence.
        """
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
    
    @staticmethod
    def filter_by_gender(questions: List[Question], gender: str = None) -> List[Question]:
        """
        Filtre selon le genre du patient ('M' ou 'F').
        """
        if not gender:
            return questions
            
        filtered = []
        for q in questions:
            if q.target_gender is None or q.target_gender == gender:
                filtered.append(q)
                
        return filtered
    
    @staticmethod
    def filter_by_age(questions: List[Question], age: int = None) -> List[Question]:
        """
        Filtre selon l'âge du patient.
        """
        if age is None:
            return questions
            
        filtered = []
        for q in questions:
            should_keep = True
            
            if q.age_min is not None and age < q.age_min:
                should_keep = False
            
            if q.age_max is not None and age > q.age_max:
                should_keep = False
            
            if should_keep:
                filtered.append(q)
                
        return filtered
    
    @staticmethod
    def filter_by_polymedicamentation(
        questions: List[Question], 
        has_other_meds: bool = False
    ) -> List[Question]:
        """
        Filtre selon si le patient prend d'autres médicaments.
        Une question avec requires_other_meds=True ne s'affiche QUE si le patient indique prendre d'autres médicaments.
        
        Note: Les questions Q_POLYMEDICAMENTATION_* sont exclues car elles redemandent 
        la même information déjà collectée dans le formulaire initial (UserProfileForm).
        """
        filtered = []
        for q in questions:
            # Exclusion des questions "Prenez-vous d'autres médicaments ?"
            # car cette info est déjà collectée en amont
            if q.id.startswith("Q_POLYMEDICAMENTATION"):
                continue
            
            # Si la question nécessite que le patient prenne d'autres médicaments
            if q.requires_other_meds and not has_other_meds:
                continue
                
            filtered.append(q)
            
        return filtered
    
    @staticmethod
    def apply_all_filters(
        questions: List[Question],
        route: str = None,
        gender: str = None,
        age: int = None,
        has_other_meds: bool = False
    ) -> List[Question]:
        """
        Applique tous les filtres en cascade.
        Retourne la liste des questions pertinentes pour le contexte patient.
        """
        result = questions
        result = QuestionFilterService.filter_by_route(result, route)
        result = QuestionFilterService.filter_by_gender(result, gender)
        result = QuestionFilterService.filter_by_age(result, age)
        result = QuestionFilterService.filter_by_polymedicamentation(result, has_other_meds)
        return result
