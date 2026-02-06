"""
Repository pour l'accès aux données d'automédication.
Responsabilité unique : communiquer avec SQLite.
"""
import sqlite3
import os
from typing import List, Optional
from backend.core.models import Question, RiskLevel


# Configuration de la base de données
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '..', 'data', 'safepills.db')


class AutomedicationRepository:
    """Data Access Object pour les questions et substances"""
    
    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: Chemin vers la base SQLite (pour tests avec DB mock)
        """
        self.db_path = db_path or DB_PATH
    
    def get_questions_by_ids(self, question_ids: List[str]) -> List[Question]:
        """
        Récupère les questions par leurs IDs.
        
        Args:
            question_ids: Liste des IDs de questions
            
        Returns:
            Liste d'objets Question
        """
        if not question_ids:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(question_ids))
            query = f"SELECT * FROM questions WHERE id IN ({placeholders})"
            
            cursor.execute(query, question_ids)
            rows = cursor.fetchall()
            
            questions = []
            for r in rows:
                try:
                    risk_enum = RiskLevel(r['risk_level'])
                except ValueError:
                    risk_enum = RiskLevel.GREEN
                
                # Parse routes et tags depuis JSON strings
                import json
                try:
                    applicable_routes_raw = r['applicable_routes'] if 'applicable_routes' in r.keys() else None
                    applicable_routes = json.loads(applicable_routes_raw) if applicable_routes_raw else []
                except (json.JSONDecodeError, TypeError):
                    applicable_routes = []
                
                try:
                    trigger_tags_raw = r['trigger_tags'] if 'trigger_tags' in r.keys() else None
                    trigger_tags = json.loads(trigger_tags_raw) if trigger_tags_raw else []
                except (json.JSONDecodeError, TypeError):
                    trigger_tags = []
                
                question = Question(
                    id=r['id'],
                    text=r['text'],
                    risk_level=risk_enum,
                    trigger_tags=trigger_tags,
                    applicable_routes=applicable_routes,
                    target_gender=r['target_gender'] if 'target_gender' in r.keys() else None,
                    age_min=r['age_min'] if 'age_min' in r.keys() else None,
                    age_max=r['age_max'] if 'age_max' in r.keys() else None,
                    requires_other_meds=bool(r['requires_other_meds']) if 'requires_other_meds' in r.keys() else False
                )
                questions.append(question)
            
            conn.close()
            return questions
            
        except Exception as e:
            print(f"Erreur get_questions_by_ids: {e}")
            return []
    
    def get_substance_tags(self, identifier: str) -> List[str]:
        """
        Récupère les tags d'une substance ou médicament.
        
        Args:
            identifier: CIS (médicament) ou Code Substance
            
        Returns:
            Liste des tags
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            import json
            
            # Essayer d'abord comme substance
            cursor.execute("SELECT tags FROM substances WHERE code = ?", (identifier,))
            row = cursor.fetchone()
            
            if row and row['tags']:
                conn.close()
                return json.loads(row['tags']) if isinstance(row['tags'], str) else row['tags']
            
            # Sinon essayer comme médicament (via drug_substances)
            query = """
                SELECT s.tags
                FROM substances s
                JOIN drug_substances ds ON s.code = ds.substance_code
                WHERE ds.drug_cis = ?
            """
            cursor.execute(query, (identifier,))
            rows = cursor.fetchall()
            
            all_tags = []
            for r in rows:
                if r['tags']:
                    tags = json.loads(r['tags']) if isinstance(r['tags'], str) else r['tags']
                    all_tags.extend(tags)
            
            conn.close()
            return list(set(all_tags))  # Dédupliquer
            
        except Exception as e:
            print(f"Erreur get_substance_tags: {e}")
            return []
    
    def get_questions_by_tags(self, tags: List[str]) -> List[Question]:
        """
        Récupère toutes les questions qui correspondent à au moins un des tags donnés.
        
        Args:
            tags: Liste des tags à matcher
            
        Returns:
            Liste d'objets Question
        """
        if not tags:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Récupérer toutes les questions et filtrer en Python (plus simple que SQL sur JSON)
            cursor.execute("SELECT * FROM questions")
            rows = cursor.fetchall()
            
            questions = []
            import json
            
            for r in rows:
                try:
                    trigger_tags_raw = r['trigger_tags'] if 'trigger_tags' in r.keys() else None
                    trigger_tags = json.loads(trigger_tags_raw) if trigger_tags_raw else []
                except (json.JSONDecodeError, TypeError):
                    trigger_tags = []
                
                # Vérifier si au moins un tag matche
                if any(tag in tags for tag in trigger_tags):
                    try:
                        risk_enum = RiskLevel(r['risk_level'])
                    except ValueError:
                        risk_enum = RiskLevel.GREEN
                    
                    try:
                        applicable_routes_raw = r['applicable_routes'] if 'applicable_routes' in r.keys() else None
                        applicable_routes = json.loads(applicable_routes_raw) if applicable_routes_raw else []
                    except (json.JSONDecodeError, TypeError):
                        applicable_routes = []
                    
                    question = Question(
                        id=r['id'],
                        text=r['text'],
                        risk_level=risk_enum,
                        trigger_tags=trigger_tags,
                        applicable_routes=applicable_routes,
                        target_gender=r['target_gender'] if 'target_gender' in r.keys() else None,
                        age_min=r['age_min'] if 'age_min' in r.keys() else None,
                        age_max=r['age_max'] if 'age_max' in r.keys() else None,
                        requires_other_meds=bool(r['requires_other_meds']) if 'requires_other_meds' in r.keys() else False
                    )
                    questions.append(question)
            
            conn.close()
            return questions
            
        except Exception as e:
            print(f"Erreur get_questions_by_tags: {e}")
            return []
    
    def get_drug_route(self, cis: str) -> Optional[str]:
        """
        Récupère la voie d'administration d'un médicament.
        
        Args:
            cis: Code CIS du médicament
            
        Returns:
            Route d'administration (ex: "ORALE") ou None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT administration_route FROM drugs WHERE cis = ?", (cis,))
            row = cursor.fetchone()
            
            conn.close()
            return row['administration_route'] if row else None
            
        except Exception as e:
            print(f"Erreur get_drug_route: {e}")
            return None
