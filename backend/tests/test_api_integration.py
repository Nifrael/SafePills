"""
Tests d'intégration API.
Utilise TestClient pour vérifier les endpoints HTTP.
"""
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.api.main import app
from backend.core.models import RiskLevel
from backend.core.schemas import EvaluationResponse

client = TestClient(app)

def test_evaluate_endpoint_serialization():
    """
    Test que l'endpoint /evaluate renvoie bien le bon JSON
    et gère correctement l'Enum RiskLevel.
    """
    # 1. On Mock le service pour ne pas taper dans la DB
    # On simule que le service répond "RED"
    mock_response = EvaluationResponse(
        score=RiskLevel.RED,
        details=["DANGER SIMULÉ"]
    )
    
    with patch("backend.api.automedication.evaluate_risk", return_value=mock_response) as mock_service:
        # 2. Appel API
        payload = {
            "cis": "12345678",
            "answers": {"Q1": True}
        }
        response = client.post("/api/automedication/evaluate", json=payload)
        
        # 3. Vérifications
        assert response.status_code == 200
        data = response.json()
        
        # Le plus important : le Frontend reçoit-il "RED" (string) ou un objet bizarre ?
        assert data["score"] == "RED" 
        assert data["details"][0] == "DANGER SIMULÉ"
        
        # Vérifions que notre mock a bien été appelé
        mock_service.assert_called_once()

def test_search_endpoint_structure():
    """
    Test simple sur la structure de retour de la recherche
    (Vérifie que le format est bien une liste d'objets standardisés)
    """
    # On mock search_medication pour renvoyer un résultat fixe
    mock_results = [
        {"id": "123", "type": "drug", "name": "TEST DRUG", "description": "Test"}
    ]
    
    with patch("backend.api.main.search_medication", return_value=mock_results):
        response = client.get("/api/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["type"] == "drug"
        assert data[0]["name"] == "TEST DRUG"
