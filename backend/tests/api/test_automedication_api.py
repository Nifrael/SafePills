"""
Tests d'intégration API mis à jour pour le Refactoring.
Couvre: 
1. Recherche (/search)
2. Flux de questions (/flow) - NOUVEAU
3. Évaluation (/evaluate)
"""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.api.main import app
from backend.core.models import RiskLevel, Question
from backend.core.schemas import EvaluationResponse, FlowQuestion, SearchResult

client = TestClient(app)

# --- MOCK DATA ---

MOCK_SEARCH_RESULT = [
    SearchResult(type="drug", id="123", name="TEST DRUG", description="Test Description")
]

MOCK_FLOW_QUESTIONS = [
    FlowQuestion(id="Q1", text="Question 1", type="boolean", is_profile=False),
    FlowQuestion(id="GENDER", text="Sexe ?", type="choice", is_profile=True)
]

MOCK_EVALUATION = EvaluationResponse(
    score=RiskLevel.RED,
    details=["DANGER SIMULÉ"],
    answered_questions_context=[]
)

# --- TESTS ---

def test_search_endpoint():
    """Vérifie que /search renvoie bien la liste attendue"""
    # Attention au chemin du patch : c'est celui IMPORTÉ dans drugs.py
    with patch("backend.api.drugs.search_medication", return_value=MOCK_SEARCH_RESULT):
        response = client.get("/api/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "TEST DRUG"

def test_flow_endpoint():
    """Vérifie que /flow renvoie bien la liste de questions unifiée"""
    # On mocke DEUX choses : les tags et les questions par tags
    # Car get_flow appelle le repository
    
    # Stratégie plus simple : on mocke carrément la fonction get_flow si on veut tester le routeur
    # MAIS ici on veut tester l'intégration. Donc on va mocker le Repository.
    
    with patch("backend.api.flow_endpoint._repository") as mock_repo:
        # 1. Mock: Tags trouvés
        mock_repo.get_substance_tags.return_value = ["TAG_TEST"]
        # 2. Mock: Questions trouvées
        mock_repo.get_questions_by_tags.return_value = [
            Question(id="Q1", text="Test Q", risk_level=RiskLevel.GREEN, trigger_tags=["TAG_TEST"])
        ]
        # 3. Mock: Route
        mock_repo.get_drug_route.return_value = "ORALE"
        
        response = client.get("/api/automedication/flow/123")
        
        # Le code doit renvoyer 200 et une liste JSON
        assert response.status_code == 200
        data = response.json()
        
        # On doit retrouver notre question Q1 + HAS_OTHER_MEDS (ajouté par défaut dans le profil)
        ids = [q["id"] for q in data]
        assert "Q1" in ids
        assert "HAS_OTHER_MEDS" in ids 

def test_evaluate_endpoint():
    """Vérifie que /evaluate appel le service et renvoie le JSON formaté"""
    # Ici on mocke la fonction evaluate_risk importée dans api.automedication
    with patch("backend.api.automedication.evaluate_risk", return_value=MOCK_EVALUATION) as mock_service:
        payload = {
            "cis": "123",
            "answers": {"Q1": True},
            "has_other_meds": False,
            "gender": "M",
            "age": 30
        }
        response = client.post("/api/automedication/evaluate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["score"] == "RED"
        assert data["details"][0] == "DANGER SIMULÉ"
        mock_service.assert_called_once()
