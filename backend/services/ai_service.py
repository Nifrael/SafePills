"""
Service IA pour la génération d'explications pédagogiques.
Utilise Google Gemini via le nouveau SDK google.genai.
"""
import os
from typing import List
from dotenv import load_dotenv
from google import genai
from google.genai import types

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
        print(f"Erreur configuration Gemini: {e}")

async def generate_risk_explanation(
    drug_name: str,
    score: str,
    details: List[str],
    user_profile: dict,
    answered_questions: List[dict] = []
) -> str:
    """
    Génère une explication bienveillante et pédagogique ultra-personnalisée.
    """
    if not client:
        return "Service d'assistance virtuelle indisponible pour le moment."

    try:
        # Construction du contexte patient enrichi
        gender_text = "une femme" if user_profile.get('gender') == 'F' else "un homme"
        age_text = f"{user_profile.get('age', '?')} ans"
        
        patient_context = f"Le patient est {gender_text} de {age_text}.\n"
        
        # Ajout des réponses aux questions
        if answered_questions:
            patient_context += "\nRéponses du patient qui déclenchent des alertes :\n"
            for q in answered_questions:
                risk_emoji = "🔴" if q['risk_level'] == 'RED' else "🟠"
                patient_context += f"{risk_emoji} {q['question_text']} → {q['answer']}\n"
        
        # Construction du prompt
        system_instruction = """Tu es un pharmacien expérimenté, bienveillant et pédagogique.
Ton patient te demande conseil pour prendre un médicament en automédication.
Le système expert a détecté des risques basés sur ses réponses à notre questionnaire médical.

Ton rôle est d'expliquer POURQUOI c'est déconseillé (ou risqué) en langage simple, sans jargon médical complexe.

RÈGLES IMPORTANTES :
- Parle directement au patient (tutoiement ou vouvoiement naturel)
- Fais référence à ses réponses spécifiques au questionnaire ("Vous nous avez indiqué que...")
- Explique concrètement les risques médicaux (pas juste "c'est dangereux")
- Termine par un conseil d'action clair (consulter un médecin, aller en pharmacie, appeler le 15 si urgence)
- Ne dis JAMAIS "selon la base de données" ou "le système a détecté"
- Sois rassurant mais ferme sur les contre-indications
- Maximum 4-5 phrases courtes"""

        user_prompt = f"""
CONTEXTE PATIENT :
{patient_context}

MÉDICAMENT DEMANDÉ : {drug_name}
NIVEAU DE RISQUE DÉTECTÉ : {score}

Explique-lui personnellement pourquoi ce n'est pas recommandé dans sa situation, en faisant référence à ses réponses.
"""
        
        # Génération avec le nouveau SDK
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7
            )
        )
        
        return response.text

    except Exception as e:
        print(f"Erreur génération IA: {e}")
        return "Désolé, je n'ai pas pu générer d'explication personnalisée pour le moment."
