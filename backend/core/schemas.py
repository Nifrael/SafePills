"""
Schemas Pydantic (DTO)
Ce sont les objets qui transitent via l'API (Entrées/Sorties),
mais qui ne sont PAS stockés tels quels en base de données.
"""
from pydantic import BaseModel
from typing import List, Optional
from .models import RiskLevel

class SearchResult(BaseModel):
    """Ce que le moteur de recherche renvoie à l'UI"""
    type: str         # "drug" ou "substance"
    id: str           # CIS ou Code Substance
    name: str
    description: Optional[str] = None

class EvaluationResponse(BaseModel):
    """Résultat du calcul/algorithme d'analyse"""
    score: RiskLevel  # Utilisation de l'Enum
    details: List[str] # Messages explicatifs générés dynamiquement
    ai_explanation: Optional[str] = None # Explication pédagogique générée par IA
    general_advice: List[str] = []  # Conseils généraux de la substance (affichés même en GREEN)
    has_coverage: bool = True  # False si aucune question n'est associée au médicament
    # Ce champ est utilisé EN INTERNE pour passer le contexte à l'IA.
    # Il ne doit PAS apparaître dans la réponse JSON envoyée au client.
    answered_questions_context: Optional[List[dict]] = None

    model_config = {
        # On exclut answered_questions_context du JSON de réponse
        "json_schema_extra": {"exclude": ["answered_questions_context"]}
    }

    def model_dump(self, **kwargs):
        """On exclut les champs internes de la sérialisation par défaut"""
        kwargs.setdefault("exclude", set())
        kwargs["exclude"] = set(kwargs["exclude"]) | {"answered_questions_context"}
        return super().model_dump(**kwargs)
