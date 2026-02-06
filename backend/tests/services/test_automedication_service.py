"""
Tests de caractérisation pour automedication_service
Ces tests capturent le comportement actuel avant refactoring (TDD Legacy Code)
"""
import pytest
from backend.core.models import Question, RiskLevel
from backend.services.automedication import (
    filter_questions_by_route,
    filter_questions_by_gender,
    filter_questions_by_age,
    filter_questions_by_polymedicamentation,
    compute_risk_score
)


class TestQuestionFilters:
    """Tests pour les fonctions de filtrage des questions"""
    
    def test_filter_by_route_keeps_oral_questions(self):
        """Une question pour voie orale doit être gardée si route='ORALE'"""
        questions = [
            Question(
                id="Q_TEST_ORAL",
                text="Test oral",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                applicable_routes=["orale"]  # En minuscules comme dans le code
            )
        ]
        
        result = filter_questions_by_route(questions, route="ORALE")
        
        assert len(result) == 1
        assert result[0].id == "Q_TEST_ORAL"
    
    def test_filter_by_route_excludes_cutanee_when_oral(self):
        """Une question pour voie cutanée doit être exclue si route='ORALE'"""
        questions = [
            Question(
                id="Q_TEST_CUTANEE",
                text="Test cutanée",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                applicable_routes=["CUTANEE"]
            )
        ]
        
        result = filter_questions_by_route(questions, route="ORALE")
        
        assert len(result) == 0
    
    def test_filter_by_route_keeps_all_if_no_route_specified(self):
        """Les questions sans route spécifiée doivent être conservées"""
        questions = [
            Question(
                id="Q_GROSSESSE",
                text="Êtes-vous enceinte ?",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                applicable_routes=[]
            )
        ]
        
        result = filter_questions_by_route(questions, route="ORALE")
        
        assert len(result) == 1
    
    def test_filter_by_route_keeps_all_if_route_none(self):
        """Si route=None, on garde tout par prudence (recherche substance)"""
        questions = [
            Question(
                id="Q_TEST",
                text="Test",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                applicable_routes=["CUTANEE"]
            )
        ]
        
        result = filter_questions_by_route(questions, route=None)
        
        assert len(result) == 1


    def test_filter_by_gender_keeps_female_questions_for_female(self):
        """Questions spécifiques femmes gardées pour genre='F'"""
        questions = [
            Question(
                id="Q_GROSSESSE",
                text="Êtes-vous enceinte ?",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                target_gender="F"
            )
        ]
        
        result = filter_questions_by_gender(questions, gender="F")
        
        assert len(result) == 1
    
    def test_filter_by_gender_excludes_female_questions_for_male(self):
        """Questions spécifiques femmes exclues pour genre='M'"""
        questions = [
            Question(
                id="Q_GROSSESSE",
                text="Êtes-vous enceinte ?",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                target_gender="F"
            )
        ]
        
        result = filter_questions_by_gender(questions, gender="M")
        
        assert len(result) == 0


    def test_filter_by_age_keeps_child_questions_for_children(self):
        """Questions enfants (<15 ans) gardées pour age=10"""
        questions = [
            Question(
                id="Q_CHILD",
                text="Question enfant",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                age_max=15  # Question pour < 15 ans
            )
        ]
        
        result = filter_questions_by_age(questions, age=10)
        
        assert len(result) == 1
    
    def test_filter_by_age_excludes_child_questions_for_adults(self):
        """Questions enfants exclues pour age=30"""
        questions = [
            Question(
                id="Q_CHILD",
                text="Question enfant",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                age_max=15  # Question pour < 15 ans
            )
        ]
        
        result = filter_questions_by_age(questions, age=30)
        
        assert len(result) == 0
    
    def test_filter_by_age_keeps_elderly_questions_for_elderly(self):
        """Questions seniors (>=65 ans) gardées pour age=70"""
        questions = [
            Question(
                id="Q_SENIOR",
                text="Question senior",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                age_min=65  # Question pour >= 65 ans
            )
        ]
        
        result = filter_questions_by_age(questions, age=70)
        
        assert len(result) == 1


    def test_filter_by_polymeds_keeps_polymeds_questions_when_has_other_meds(self):
        """Questions polymédication gardées si has_other_meds=True"""
        questions = [
            Question(
                id="Q_POLYMEDS",
                text="Interactions médicamenteuses",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                requires_other_meds=True
            )
        ]
        
        result = filter_questions_by_polymedicamentation(questions, has_other_meds=True)
        
        assert len(result) == 1
    
    def test_filter_by_polymeds_excludes_polymeds_questions_when_no_other_meds(self):
        """Questions polymédication exclues si has_other_meds=False"""
        questions = [
            Question(
                id="Q_POLYMEDS",
                text="Interactions médicamenteuses",
                risk_level=RiskLevel.RED,
                trigger_tags=[],
                requires_other_meds=True
            )
        ]
        
        result = filter_questions_by_polymedicamentation(questions, has_other_meds=False)
        
        assert len(result) == 0


class TestRiskScoreCalculation:
    """Tests pour le calcul du score de risque (logique métier pure)"""
    
    def test_compute_risk_all_no_answers_returns_green(self):
        """Si toutes les réponses sont NON, score = GREEN"""
        questions = [
            Question(
                id="Q_GROSSESSE",
                text="Êtes-vous enceinte ?",
                risk_level=RiskLevel.RED,
                trigger_tags=[]
            ),
            Question(
                id="Q_HEPATIQUE",
                text="Problèmes hépatiques ?",
                risk_level=RiskLevel.ORANGE,
                trigger_tags=[]
            )
        ]
        
        answers = {
            "Q_GROSSESSE": False,
            "Q_HEPATIQUE": False
        }
        
        result = compute_risk_score(questions, answers)
        
        assert result.score == RiskLevel.GREEN
        assert len(result.details) == 0
    
    def test_compute_risk_one_red_answer_returns_red(self):
        """Si une réponse OUI à une question RED, score = RED"""
        questions = [
            Question(
                id="Q_GROSSESSE",
                text="Êtes-vous enceinte ?",
                risk_level=RiskLevel.RED,
                trigger_tags=[]
            )
        ]
        
        answers = {
            "Q_GROSSESSE": True
        }
        
        result = compute_risk_score(questions, answers)
        
        assert result.score == RiskLevel.RED
        assert any("ALERTE ROUGE" in d for d in result.details)
    
    def test_compute_risk_one_orange_answer_returns_orange(self):
        """Si une réponse OUI à une question ORANGE, score = ORANGE"""
        questions = [
            Question(
                id="Q_HEPATIQUE",
                text="Problèmes hépatiques ?",
                risk_level=RiskLevel.ORANGE,
                trigger_tags=[]
            )
        ]
        
        answers = {
            "Q_HEPATIQUE": True
        }
        
        result = compute_risk_score(questions, answers)
        
        assert result.score == RiskLevel.ORANGE
        assert any("Attention" in d for d in result.details)
    
    def test_compute_risk_red_overrides_orange(self):
        """RED a la priorité sur ORANGE"""
        questions = [
            Question(
                id="Q_GROSSESSE",
                text="Êtes-vous enceinte ?",
                risk_level=RiskLevel.RED,
                trigger_tags=[]
            ),
            Question(
                id="Q_HEPATIQUE",
                text="Problèmes hépatiques ?",
                risk_level=RiskLevel.ORANGE,
                trigger_tags=[]
            )
        ]
        
        answers = {
            "Q_GROSSESSE": True,
            "Q_HEPATIQUE": True
        }
        
        result = compute_risk_score(questions, answers)
        
        assert result.score == RiskLevel.RED
        # Le comportement actuel arrête au premier RED
        assert len(result.details) >= 1
        assert any("ROUGE" in d for d in result.details)
    
    def test_compute_risk_unanswered_questions_ignored(self):
        """Les questions non répondues ne doivent pas affecter le score"""
        questions = [
            Question(
                id="Q_GROSSESSE",
                text="Êtes-vous enceinte ?",
                risk_level=RiskLevel.RED,
                trigger_tags=[]
            ),
            Question(
                id="Q_HEPATIQUE",
                text="Problèmes hépatiques ?",
                risk_level=RiskLevel.ORANGE,
                trigger_tags=[]
            )
        ]
        
        answers = {
            "Q_GROSSESSE": False
            # Q_HEPATIQUE non répondue
        }
        
        result = compute_risk_score(questions, answers)
        
        assert result.score == RiskLevel.GREEN
