from pydantic import BaseModel, Field
from typing import List, Optional

class Substance(BaseModel):
    """
    Représente une substance active contenue dans un médicament.
    Exemple: Paracétamol
    """
    substance_code: str
    name: str
    dose: Optional[str] = None
    therapeutic_class: Optional[str] = None

class Drug(BaseModel):
    """
    Représente un médicament simplifié pour la recherche et les interactions.
    """
    cis: str
    name: str
    substances: List[Substance] = []

class InteractionRule(BaseModel):
    """
    Ce modèle représente une règle d'interaction extraite du thésaurus.
    Il sert de base à la validation SQL et de contexte pour l'IA.
    """
    level_alert: str  # Contre-indication, Association déconseillée, etc.
    risk: str
    advice: str
    source: str = "Thésaurus ANSM"

class SafePillsAnalysis(BaseModel):
    """
    C'est le MODÈLE FINAL que l'IA (Gemini) devra remplir.
    Ce format sera identique pour toutes les réponses (Standardisation).
    """
    interaction_detected: bool
    level_alert: Optional[str] = None # Rouge (CI), Orange (AD), Jaune (PE)
    explanation: str = Field(..., description="Explication simple en français ou espagnol")
    conduct_to_follow: str
    habits_risks: Optional[str] = None # Alcool, soleil, alimentation