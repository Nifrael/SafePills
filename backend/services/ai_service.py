import os
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv
from google import genai
from google.genai import types

from backend.core.i18n import i18n

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, '..', '..')
load_dotenv(os.path.join(ROOT_DIR, '.env'))

GOOGLE_API_KEY = os.getenv("API_KEY")

client = None
if GOOGLE_API_KEY:
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        logger.error(f"Erreur configuration Gemini: {e}")

KNOWLEDGE_PATH = os.path.join(BASE_DIR, '..', 'data', 'medical_knowledge.json')
SUBSTANCE_ADVICE: Dict = {}

try:
    with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
        knowledge = json.load(f)
        SUBSTANCE_ADVICE = knowledge.get('substance_advice', {})
    logger.info(f"Conseils pharmaceutiques chargés ({len(SUBSTANCE_ADVICE)} substances)")
except Exception as e:
    logger.warning(f"Impossible de charger les conseils: {e}")


def _collect_advice(
    substance_names: List[str],
    triggered_question_ids: List[str],
    lang: str = "fr"
) -> str:
    advice_lines = []

    for substance in substance_names:
        # Get general advice via i18n
        for tip in i18n.get_advice(substance, "general", lang):
             advice_lines.append(f"- {tip}")

        for q_id in triggered_question_ids:
            base_id = q_id
            for suffix in ['_RED_F', '_ORANGE_F', '_GREEN_F', '_RED', '_ORANGE', '_GREEN']:
                if q_id.endswith(suffix):
                    base_id = q_id[:-len(suffix)]
                    break
            
            # Get specific advice via i18n
            for tip in i18n.get_advice(substance, base_id, lang):
                if f"- {tip}" not in advice_lines:  
                    advice_lines.append(f"- {tip}")

    return '\n'.join(advice_lines)


def get_general_advice(substance_names: List[str], lang: str = "fr") -> List[str]:
    general_tips = []
    for sub in substance_names:
        tips = i18n.get_advice(sub, "general", lang)
        for tip in tips:
            if tip not in general_tips:
                general_tips.append(tip)
    return general_tips


async def generate_risk_explanation(
    drug_name: str,
    score: str,
    details: List[str],
    user_profile: dict,
    answered_questions: List[dict] = [],
    lang: str = "fr"
) -> str:
    if not client:
        return "Service d'assistance virtuelle indisponible pour le moment." if lang == "fr" else "Servicio de asistencia virtual no disponible por el momento."

    try:
        # Profile context
        if lang == "es":
            gender_text = "una mujer" if user_profile.get('gender') == 'F' else "un hombre"
            age_text = f"{user_profile.get('age', '?')} años"
            patient_context = f"El paciente es {gender_text} de {age_text}.\n"
            
            if answered_questions:
                patient_context += "\nRespuestas del paciente que activan alertas:\n"
                for q in answered_questions:
                    risk_emoji = "🔴" if q['risk_level'] == 'RED' else "🟠"
                    patient_context += f"{risk_emoji} {q['question_text']} → {q['answer']}\n"
        else:
            gender_text = "une femme" if user_profile.get('gender') == 'F' else "un homme"
            age_text = f"{user_profile.get('age', '?')} ans"
            patient_context = f"Le patient est {gender_text} de {age_text}.\n"
            
            if answered_questions:
                patient_context += "\nRéponses du patient qui déclenchent des alertes :\n"
                for q in answered_questions:
                    risk_emoji = "🔴" if q['risk_level'] == 'RED' else "🟠"
                    patient_context += f"{risk_emoji} {q['question_text']} → {q['answer']}\n"

        substance_names = user_profile.get('substances', [])
        triggered_ids = [q['question_id'] for q in answered_questions if q.get('question_id')]
        
        validated_advice = _collect_advice(substance_names, triggered_ids, lang)
        
        logger.debug(f"RAG — Substances: {substance_names}")
        logger.debug(f"RAG — Questions déclenchées: {triggered_ids}")
        logger.debug(f"RAG — Conseils trouvés: {len(validated_advice.splitlines())} lignes")

        if lang == "es":
            system_instruction = """Eres un farmacéutico experimentado, amable y pedagógico.
Tu paciente te pide consejo para tomar un medicamento en automedicación.

REGLAS STRICTAS:
- Basa tu respuesta EXCLUSIVAMENTE en los elementos de consejo proporcionados a continuación.
- NO inventes NINGUNA información médica que no figure en estos elementos.
- Habla directamente al paciente (usted)
- Haz referencia a sus respuestas específicas ("Nos ha indicado que...")
- Explica concretamente los riesgos en lenguaje sencillo
- Termina con un consejo de acción claro (consultar a un farmacéutico, un médico, etc.)
- NUNCA digas "según la base de datos" o "el sistema ha detectado"
- Sé tranquilizador pero firme sobre las contraindicaciones
- RESPONDE EN ESPAÑOL
- Máximo 5 frases cortas y claras"""

            user_prompt = f"""
CONTEXTO PACIENTE:
{patient_context}

MEDICAMENTO SOLICITADO: {drug_name}
NIVEL DE RIESGO DETECTADO: {score}
"""
            if validated_advice:
                user_prompt += f"""
ELEMENTOS DE CONSEJO VALIDADOS A UTILIZAR:
{validated_advice}

Reformule estos elementos en una explicación personalizada para este paciente, teniendo en cuenta su perfil y respuestas.
"""
            else:
                user_prompt += """
Explique por qué no es recomendado en su situación, manteniéndose factual y amable.
"""

        else:
            system_instruction = """Tu es un pharmacien expérimenté, bienveillant et pédagogique.
Ton patient te demande conseil pour prendre un médicament en automedicación.

RÈGLES STRICTES :
- Base ta réponse EXCLUSIVAMENTE sur les éléments de conseil fournis ci-dessous.
- N'invente AUCUNE information médicale qui ne figure pas dans ces éléments.
- Parle directement au patient (vouvoiement)
- Fais référence à ses réponses spécifiques ("Vous nous avez indiqué que...")
- Explique concrètement les risques en langage simple
- Termine par un conseil d'action clair (consulter un pharmacien, un médecin, etc.)
- Ne dis JAMAIS "selon la base de données" ou "le système a détecté"
- Sois rassurant mais ferme sur les contre-indications
- Maximum 5 phrases courtes et claires"""

            user_prompt = f"""
CONTEXTE PATIENT :
{patient_context}

MÉDICAMENT DEMANDÉ : {drug_name}
NIVEAU DE RISQUE DÉTECTÉ : {score}
"""
            if validated_advice:
                user_prompt += f"""
ÉLÉMENTS DE CONSEIL VALIDÉS À UTILISER :
{validated_advice}

Reformule ces éléments en une explication personnalisée pour ce patient, en tenant compte de son profil et de ses réponses.
"""
            else:
                user_prompt += """
Explique-lui pourquoi ce n'est pas recommandé dans sa situation, en restant factuel et bienveillant.
"""
        
        response = client.models.generate_content(
            model='gemini-flash-latest',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3
            )
        )
        
        return response.text

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            logger.warning(f"Quota IA dépassé: {e}")
            return "Le service d'analyse par IA est temporairement surchargé. Veuillez réessayer dans quelques instants." if lang == "fr" else "El servicio de análisis por IA está temporalmente sobrecargado. Por favor, inténtelo de nuevo en unos momentos."
        
        logger.error(f"Erreur génération IA: {e}", exc_info=True)
        return "Désolé, je n'ai pas pu générer d'explication personnalisée pour le moment." if lang == "fr" else "Lo siento, no pude generar una explicación personalizada en este momento."
