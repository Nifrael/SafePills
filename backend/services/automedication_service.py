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

from ..core.schemas import EvaluationResponse
from ..core.models import Question, RiskLevel

# ...

def compute_risk_score(questions: List[Question], answers: Dict[str, bool]) -> EvaluationResponse:
    """
    Fonction PURE : Calcule le score basé uniquement sur les inputs.
    Aucun accès DB ici. Testable unitairement.
    """
    score = RiskLevel.GREEN
    details = []
    
    # On indexe les questions par ID pour accès rapide
    questions_map = {q.id: q for q in questions}
    
    for q_id, is_yes in answers.items():
        if is_yes and q_id in questions_map:
            question = questions_map[q_id]
            risk = question.risk_level
            
            # Logique de Max Risque : RED > ORANGE > GREEN
            if risk == RiskLevel.RED:
                score = RiskLevel.RED
                details.append(f"ALERTE ROUGE : {question.text} (Contre-indication formelle)")
            elif risk == RiskLevel.ORANGE and score != RiskLevel.RED:
                score = RiskLevel.ORANGE
                details.append(f"Attention : {question.text} (Précautions requises)")
                
    if score == RiskLevel.GREEN:
        # On ne met un message positif que s'il n'y a pas d'alerte
        pass 
        
    return EvaluationResponse(score=score, details=details)

def evaluate_risk(answers: Dict[str, bool]) -> EvaluationResponse:
    """
    Orchestrateur : Récupère les données DB -> Appelle la logique pure.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        answered_ids = list(answers.keys())
        if not answered_ids:
             return EvaluationResponse(score=RiskLevel.GREEN, details=[])

        # Construction dynamique de la requête IN (?,?,?)
        placeholders = ','.join('?' * len(answered_ids))
        query = f"SELECT * FROM questions WHERE id IN ({placeholders})"
        
        cursor.execute(query, answered_ids)
        rows = cursor.fetchall()
        
        questions = []
        for r in rows:
            # Conversion String (DB) -> Enum (Model)
            # Si la DB contient une valeur inconnue, cela lèvera une erreur (sécurité)
            try:
                risk_enum = RiskLevel(r['risk_level'])
            except ValueError:
                risk_enum = RiskLevel.GREEN # Fallback safe ou log error
                
            questions.append(Question(
                id=r['id'],
                text=r['text'],
                risk_level=risk_enum,
                trigger_tags=[] 
            ))
            
        conn.close()
        
        # Appel de la logique Pure
        return compute_risk_score(questions, answers)
            
    except Exception as e:
        print(f"Erreur evaluate_risk: {e}")
        return EvaluationResponse(score=RiskLevel.RED, details=["Erreur technique lors de l'analyse"])
