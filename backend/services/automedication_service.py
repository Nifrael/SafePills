"""
Service d'Automédication Simplifié (KISS)
Analyse les risques basés sur les tags des substances.
"""
import sqlite3
import os
import json
from typing import List, Dict
from ..core.schemas import EvaluationResponse
from ..core.models import Question

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'safepills.db')

def get_questions_for_drug(identifier: str) -> List[Question]:
    """
    Récupère les questions pertinentes.
    L'identifiant peut être un CIS (médicament) ou un Code Substance.
    """
    questions = []
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        active_tags = set()
        
        # Cas 1 : Identifier est un CIS (numérique, ~8 chiffres)
        if identifier.isdigit() and len(identifier) >= 7:
            cursor.execute("""
                SELECT s.tags 
                FROM substances s
                JOIN drug_substances ds ON s.code = ds.substance_code
                WHERE ds.drug_cis = ?
            """, (identifier,))
        
        # Cas 2 : Identifier est un code substance (ex: "IBUPROFÈNE" ou code alphanumérique)
        else:
            cursor.execute("SELECT tags FROM substances WHERE code = ?", (identifier,))
            
        rows = cursor.fetchall()
        for row in rows:
            if row['tags']:
                try:
                    tags_list = json.loads(row['tags'])
                    for t in tags_list:
                        active_tags.add(t)
                except:
                    pass
        
        # Si aucun tag, pas de questions spécifiques
        if not active_tags:
            conn.close()
            return []
            
        # 2. Récupérer les questions qui matchent ces tags
        cursor.execute("SELECT * FROM questions")
        all_questions = cursor.fetchall()
        
        for q_row in all_questions:
            trigger_tags = []
            if q_row['trigger_tags']:
                try:
                    trigger_tags = json.loads(q_row['trigger_tags'])
                except:
                    pass
            
            if "*" in trigger_tags or not set(trigger_tags).isdisjoint(active_tags):
                questions.append(Question(
                    id=q_row['id'],
                    text=q_row['text'],
                    risk_level=q_row['risk_level'],
                    trigger_tags=trigger_tags
                ))
                
        conn.close()
        
    except Exception as e:
        print(f"Erreur get_questions: {e}")
        return []
        
    return questions

def evaluate_risk(answers: Dict[str, bool]) -> EvaluationResponse:
    """
    Calcule le score final basé sur les réponses OUI/NON.
    answers = {"Q_FOIE": True, "Q_GROSSE": False}
    """
    score = "GREEN"
    details = []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        for q_id, response in answers.items():
            if response is True: # Si l'utilisateur a répondu OUI -> Risque potentiel
                cursor.execute("SELECT risk_level, text FROM questions WHERE id = ?", (q_id,))
                row = cursor.fetchone()
                if row:
                    risk = row['risk_level']
                    # Logique de Max Risque : RED > ORANGE > GREEN
                    if risk == "RED":
                        score = "RED"
                        details.append(f"ALERTE ROUGE : {row['text']} (Contre-indication formelle)")
                    elif risk == "ORANGE" and score != "RED":
                        score = "ORANGE"
                        details.append(f"Attention : {row['text']} (Précautions requises)")
                        
        conn.close()
        
        if score == "GREEN":
            details.append("Aucune contre-indication détectée pour votre profil.")
            
    except Exception as e:
        print(f"Erreur evaluate_risk: {e}")
        return EvaluationResponse(score="RED", details=["Erreur technique lors de l'analyse"])
        
    return EvaluationResponse(score=score, details=details)
