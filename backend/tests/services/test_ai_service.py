from unittest.mock import patch, MagicMock
from backend.services.ai_service import get_general_advice, _collect_advice, generate_risk_explanation

MOCK_KNOWLEDGE = {
    "PARACETAMOL": {
        "general": ["Attention au foie", "Max 3g/jour"],
        "Q_LIVER": ["Contre-indiqué en cas d'insuffisance hépatique"],
        "Q_ALCOHOL": ["Pas d'alcool"]
    },
    "IBUPROFENE": {
        "general": ["Prendre en mangeant", "Pas enceinte"],
    }
}

def test_get_general_advice():
    with patch("backend.services.ai_service.SUBSTANCE_ADVICE", MOCK_KNOWLEDGE):
        advice = get_general_advice(["PARACETAMOL"])
        assert len(advice) == 2
        assert "Attention au foie" in advice
        
        advice_combo = get_general_advice(["PARACETAMOL", "IBUPROFENE"])
        assert len(advice_combo) == 4
        assert "Prendre en mangeant" in advice_combo
        
        advice_empty = get_general_advice(["KRYPTONITE"])
        assert advice_empty == []

def test_collect_advice_rag_logic():
    with patch("backend.services.ai_service.SUBSTANCE_ADVICE", MOCK_KNOWLEDGE):
        triggered_questions = ["Q_LIVER_RED"] 
        
        text = _collect_advice(["PARACETAMOL"], triggered_questions)
        
        assert "- Attention au foie" in text
        assert "- Contre-indiqué en cas d'insuffisance hépatique" in text
        assert "Pas d'alcool" not in text

import pytest

import asyncio

def test_generate_risk_explanation_calls_client():
    
    async def run_test():
        with patch("backend.services.ai_service.client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = "Explication générée par IA"
            
            mock_client.models.generate_content.return_value = mock_response
            
            with patch("backend.services.ai_service._collect_advice", return_value="- Conseil Mock"):
                result = await generate_risk_explanation(
                    drug_name="Test Drug",
                    score="ORANGE",
                    details=["Détail 1"],
                    user_profile={"gender": "M", "age": 30, "substances": ["PARACETAMOL"]}
                )
                
                assert result == "Explication générée par IA"
                
                mock_client.models.generate_content.assert_called_once()
                call_args = mock_client.models.generate_content.call_args
                assert "Conseil Mock" in call_args.kwargs['config'].system_instruction or "Conseil Mock" in call_args.kwargs['contents']

    asyncio.run(run_test())

