"""
Service IA pour la génération d'explications pédagogiques.
Utilise Google Gemini via le SDK google.genai.

LOGIQUE RAG (Retrieval-Augmented Generation) :
  1. On lit les conseils validés dans medical_knowledge.json
  2. On sélectionne ceux qui correspondent à la substance + aux questions déclenchées
  3. On les injecte dans le prompt Gemini
  → L'IA reformule avec TES données, elle n'invente rien.
"""
import os
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# Chargement explicite du .env à la racine du projet
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, '..', '..')
load_dotenv(os.path.join(ROOT_DIR, '.env'))

# Récupération de la clé API
GOOGLE_API_KEY = os.getenv("API_KEY")

# Configuration du client Gemini
client = None
if GOOGLE_API_KEY:
    try:
        client = genai.Client(api_key=GOOGLE_API_KEY)
    except Exception as e:
        logger.error(f"Erreur configuration Gemini: {e}")

# -----------------------------------------------------------
# CHARGEMENT DES CONSEILS (une seule fois au démarrage)
# -----------------------------------------------------------
# On lit medical_knowledge.json et on garde la section substance_advice.
# Comme c'est chargé une seule fois quand le serveur démarre, 
# il n'y a pas d'impact sur les performances.
# -----------------------------------------------------------

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
    triggered_question_ids: List[str]
) -> str:
    """
    Sélectionne les conseils pertinents pour cette situation.
    
    Paramètres :
    - substance_names : les substances du médicament (ex: ["PARACÉTAMOL"])
    - triggered_question_ids : les IDs des questions où le patient a répondu OUI
      (ex: ["Q_POLYMEDICATION", "Q_LIVER"])
    
    Retourne une chaîne de texte avec tous les conseils à injecter dans le prompt.
    S'il n'y a aucun conseil, retourne une chaîne vide.
    """
    advice_lines = []

    for substance in substance_names:
        # Chercher les conseils pour cette substance
        substance_advice = SUBSTANCE_ADVICE.get(substance, {})
        if not substance_advice:
            continue

        # 1. Toujours ajouter les conseils "general"
        for tip in substance_advice.get('general', []):
            advice_lines.append(f"- {tip}")

        # 2. Ajouter les conseils spécifiques aux questions déclenchées
        #    Ex: si le patient a déclenché Q_POLYMEDICATION,
        #    on ajoute les conseils sous la clé "Q_POLYMEDICATION"
        for q_id in triggered_question_ids:
            # On extrait l'ID de base (sans le suffixe _RED, _ORANGE, _GREEN, _F)
            # Ex: "Q_POLYMEDICATION_ORANGE" → "Q_POLYMEDICATION"
            base_id = q_id
            for suffix in ['_RED_F', '_ORANGE_F', '_GREEN_F', '_RED', '_ORANGE', '_GREEN']:
                if q_id.endswith(suffix):
                    base_id = q_id[:-len(suffix)]
                    break

            for tip in substance_advice.get(base_id, []):
                if f"- {tip}" not in advice_lines:  # Éviter les doublons
                    advice_lines.append(f"- {tip}")

    return '\n'.join(advice_lines)


async def generate_risk_explanation(
    drug_name: str,
    score: str,
    details: List[str],
    user_profile: dict,
    answered_questions: List[dict] = []
) -> str:
    """
    Génère une explication bienveillante et pédagogique ultra-personnalisée.
    
    CHANGEMENT PRINCIPAL (RAG) :
    Avant → L'IA inventait sa réponse à partir de ses connaissances d'entraînement.
    Après → L'IA reformule les conseils validés qu'on lui fournit.
    """
    if not client:
        return "Service d'assistance virtuelle indisponible pour le moment."

    try:
        # --- 1. Contexte patient (inchangé) ---
        gender_text = "une femme" if user_profile.get('gender') == 'F' else "un homme"
        age_text = f"{user_profile.get('age', '?')} ans"
        
        patient_context = f"Le patient est {gender_text} de {age_text}.\n"
        
        if answered_questions:
            patient_context += "\nRéponses du patient qui déclenchent des alertes :\n"
            for q in answered_questions:
                risk_emoji = "🔴" if q['risk_level'] == 'RED' else "🟠"
                patient_context += f"{risk_emoji} {q['question_text']} → {q['answer']}\n"

        # --- 2. NOUVEAU : Collecte des conseils validés ---
        substance_names = user_profile.get('substances', [])
        triggered_ids = [q['question_id'] for q in answered_questions if q.get('question_id')]
        
        validated_advice = _collect_advice(substance_names, triggered_ids)
        
        # Debug log (visible dans la console du serveur)
        logger.debug(f"RAG — Substances: {substance_names}")
        logger.debug(f"RAG — Questions déclenchées: {triggered_ids}")
        logger.debug(f"RAG — Conseils trouvés: {len(validated_advice.splitlines())} lignes")

        # --- 3. Construction du prompt (modifié) ---
        system_instruction = """Tu es un pharmacien expérimenté, bienveillant et pédagogique.
Ton patient te demande conseil pour prendre un médicament en automédication.

RÈGLES STRICTES :
- Base ta réponse EXCLUSIVEMENT sur les éléments de conseil fournis ci-dessous.
- N'invente AUCUNE information médicale qui ne figure pas dans ces éléments.
- Parle directement au patient (vouvoiement)
- Fais référence à ses réponses spécifiques ("Vous nous avez indiqué que...")
- Explique concrètement les risques en langage simple
- Termine par un conseil d'action clair (consulter un pharmacien, un médecin, etc.)
- Ne dis JAMAIS "selon la base de données" ou "le système a détecté"
- Sois rassurant mais ferme sur les contre-indications
- Maximum 5 phrases courtes et claires"""

        # Construction du prompt utilisateur
        user_prompt = f"""
CONTEXTE PATIENT :
{patient_context}

MÉDICAMENT DEMANDÉ : {drug_name}
NIVEAU DE RISQUE DÉTECTÉ : {score}
"""

        # Injection des conseils validés (le cœur du RAG)
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
        
        # --- 4. Appel à Gemini (inchangé, sauf temperature réduite) ---
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3  # Réduit de 0.7 → 0.3 pour rester plus factuel
            )
        )
        
        return response.text

    except Exception as e:
        logger.error(f"Erreur génération IA: {e}", exc_info=True)
        return "Désolé, je n'ai pas pu générer d'explication personnalisée pour le moment."
