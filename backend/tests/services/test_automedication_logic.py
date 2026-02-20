"""
Tests unitaires pour la logique métier de l'automédication.
Objectif : Valider le calcul de score SANS base de données.
"""
from backend.core.models import Rule, RiskLevel
from backend.services.automedication.risk_calculator import RiskCalculator
from backend.api.flow_endpoint import _convert_rules_to_questions

def test_cliptol_scenario_red_flag():
    """
    Scénario : Utilisateur prend du Cliptol (Ibuprofène)
    Il répond OUI à la question "Êtes-vous enceinte ?" (Qui est RED)
    Attendu : Score RED
    """
    rules = [
        Rule(id=1, question_code="Q_GROSSESSE", risk_level=RiskLevel.LEVEL_4, advice="Enceinte ?"),
        Rule(id=2, question_code="Q_FOIE", risk_level=RiskLevel.LEVEL_3, advice="Foie ?")
    ]
    
    answers = {
        "Q_GROSSESSE": True,
        "Q_FOIE": False
    }
    
    result = RiskCalculator.compute_score(rules, answers)
    
    assert result.score == "RED"
    assert "Enceinte ?" in result.details[0]

def test_safe_scenario_green_flag():
    """
    Scénario : Utilisateur sain
    Attendu : Score GREEN
    """
    rules = [
        Rule(id=1, question_code="Q_GROSSESSE", risk_level=RiskLevel.LEVEL_4, advice="...")
    ]
    answers = { "Q_GROSSESSE": False }
    
    result = RiskCalculator.compute_score(rules, answers)
    
    assert result.score == "GREEN"
    assert len(result.details) == 0

def test_question_filtering_by_route():
    """
    Test du filtrage des questions selon la voie d'administration.
    """
    rules = [
        Rule(id=1, question_code="Q_ULCERE", risk_level=RiskLevel.LEVEL_4, advice="Ulcère ?", filter_route="orale"),
        Rule(id=2, question_code="Q_ALLERGIE", risk_level=RiskLevel.LEVEL_4, advice="Allergie ?")
    ]
    
    # Cas 1 : Voie Orale -> Doit garder les 2 questions
    filtered_oral = _convert_rules_to_questions(rules, "orale")
    assert len(filtered_oral) == 2
    
    # Cas 2 : Voie Cutanée -> Doit rejeter Ulcère, garder Allergie
    filtered_cutanee = _convert_rules_to_questions(rules, "cutanée")
    assert len(filtered_cutanee) == 1
    assert filtered_cutanee[0].id == "Q_ALLERGIE"
