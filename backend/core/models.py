"""
Modèles de Données (Entités)
Ces objets représentent la structure des données stockées en base de données.
"""
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

# Définition propre des niveaux de risque
class RiskLevel(str, Enum):
    RED = "RED"       # Contre-indication absolue
    ORANGE = "ORANGE" # Précaution nécessaire
    GREEN = "GREEN"   # Pas de signal

# --- ENTITÉS STOCKÉES ---

class Substance(BaseModel):
    """Reflet de la table 'substances'"""
    code: str
    name: str
    tags: List[str] = []

class Drug(BaseModel):
    """Reflet de la table 'drugs'"""
    cis: str
    name: str
    administration_route: Optional[str] = None
    is_otc: bool
    # Note: En base SQL, c'est une relation. Ici pour l'objet métier, on inclut la liste.
    substances: List[Substance] = []

class Question(BaseModel):
    """Reflet de la table 'questions'"""
    id: str
    text: str
    trigger_tags: List[str] = [] # JSON stocké en base
    risk_level: RiskLevel