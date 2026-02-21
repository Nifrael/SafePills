import logging
from typing import Dict, Optional, List

from backend.core.schemas import EvaluationResponse
from backend.services.automedication import evaluate_risk
from backend.services.automedication.db_repository import AutomedicationRepository
from backend.services.search import get_drug_details
from backend.services.ai_service import generate_risk_explanation

logger = logging.getLogger(__name__)


class AutomedicationOrchestrator:

    def __init__(self, repository: AutomedicationRepository = None):
        self._repository = repository or AutomedicationRepository()

    async def evaluate(
        self,
        cis: Optional[str],
        answers: Dict[str, bool],
        has_other_meds: bool,
        gender: Optional[str],
        age: Optional[int],
        lang: str = "fr"
    ) -> EvaluationResponse:
        result = evaluate_risk(
            answers=answers,
            identifier=cis,
            has_other_meds=has_other_meds,
            lang=lang
        )

        drug_name, substance_names, is_otc = self._get_drug_info(cis, lang)

        result.general_advice = []

        if not is_otc:
            warning_msg = "⚠️ Ce médicament nécessite normalement une prescription médicale."
            if warning_msg not in result.details:
                result.details.insert(0, warning_msg)

        if cis:
            rules = self._repository.get_rules_for_brand(cis)
            result.has_coverage = len(rules) > 0
        else:
            result.has_coverage = False

        if result.score != "GREEN":
            explanation = await generate_risk_explanation(
                drug_name=drug_name,
                score=result.score,
                details=result.details,
                user_profile={
                    "gender": gender,
                    "age": age,
                    "has_other_meds": has_other_meds,
                    "substances": substance_names
                },
                answered_questions=result.answered_questions_context or [],
                lang=lang
            )
            result.ai_explanation = explanation

        return result

    def _get_drug_info(self, cis: Optional[str], lang: str) -> tuple:
        drug_name = "ce médicament" if lang == "fr" else "este medicamento"
        substance_names = []
        is_otc = True

        if cis:
            drug_info = get_drug_details(cis)
            if drug_info:
                drug_name = drug_info.name
                is_otc = drug_info.is_otc
                substance_names = [bs.substance.name for bs in drug_info.composition]

        return drug_name, substance_names, is_otc
