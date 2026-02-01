"""
Tests unitaires pour la logique métier de l'automédication.
Objectif : Valider le calcul de score SANS base de données.
"""
from backend.core.models import Question, RiskLevel
from backend.services.automedication_service import compute_risk_score

def test_cliptol_scenario_red_flag():
    """
    Scénario : Utilisateur prend du Cliptol (Ibuprofène)
    Il répond OUI à la question "Êtes-vous enceinte ?" (Qui est RED)
    Attendu : Score RED
    """
    # 1. Données d'entrée (Simulées, pas de DB !)
    # On simule les questions déclenchées
    questions = [
        Question(id="Q_GROSSESSE", text="Enceinte ?", risk_level=RiskLevel.RED, trigger_tags=["grossesse"]),
        Question(id="Q_FOIE", text="Foie ?", risk_level=RiskLevel.ORANGE, trigger_tags=["foie"])
    ]
    
    # L'utilisateur répond OUI à la grossesse (RED) et NON au foie
    answers = {
        "Q_GROSSESSE": True,
        "Q_FOIE": False
    }
    
    # 2. Appel de la fonction (Pure logique)
    result = compute_risk_score(questions, answers)
    
    # 3. Vérification (Le "Assert")
    assert result.score == RiskLevel.RED
    assert "Enceinte ?" in result.details[0] # On veut que le détail mentionne la cause

def test_safe_scenario_green_flag():
    """
    Scénario : Utilisateur sain
    Attendu : Score GREEN
    """
    questions = [
        Question(id="Q_GROSSESSE", text="...", risk_level=RiskLevel.RED, trigger_tags=[])
    ]
    answers = { "Q_GROSSESSE": False }
    
    result = compute_risk_score(questions, answers)
    
    assert result.score == RiskLevel.GREEN
    assert len(result.details) == 0 # Pas d'alerte
