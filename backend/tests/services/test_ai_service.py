from unittest.mock import patch, MagicMock, AsyncMock
from backend.services.ai_service import generate_risk_explanation
import pytest
import asyncio

def test_generate_risk_explanation_calls_client():
    
    async def run_test():
        with patch("backend.services.ai_service.client") as mock_client:
            mock_response = MagicMock()
            mock_response.text = "Explication générée par IA"
            
            mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
            
            result = await generate_risk_explanation(
                drug_name="Test Drug",
                score="ORANGE",
                details=["Détail 1"],
                user_profile={"gender": "M", "age": 30, "substances": ["PARACETAMOL"]}
            )
            
            assert result == "Explication générée par IA"
            
            mock_client.aio.models.generate_content.assert_called_once()
            call_args = mock_client.aio.models.generate_content.call_args
            assert "Détail 1" in call_args.kwargs['contents']

    asyncio.run(run_test())


