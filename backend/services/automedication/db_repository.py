import sqlite3
import os
import logging
from typing import List, Optional
from backend.core.models import Question, RiskLevel

logger = logging.getLogger(__name__)

from backend.core.config import settings
DB_PATH = settings.DB_PATH


class AutomedicationRepository:
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
    
    def _map_row_to_question(self, row) -> Question:
        """Helper: Transforme une ligne SQLite en objet Question"""
        import json
        
        try:
            risk_enum = RiskLevel(row['risk_level'])
        except ValueError:
            risk_enum = RiskLevel.GREEN
        
        try:
            applicable_routes_raw = row['applicable_routes'] if 'applicable_routes' in row.keys() else None
            applicable_routes = json.loads(applicable_routes_raw) if applicable_routes_raw else []
        except (json.JSONDecodeError, TypeError):
            applicable_routes = []
        
        try:
            trigger_tags_raw = row['trigger_tags'] if 'trigger_tags' in row.keys() else None
            trigger_tags = json.loads(trigger_tags_raw) if trigger_tags_raw else []
        except (json.JSONDecodeError, TypeError):
            trigger_tags = []
        
        return Question(
            id=row['id'],
            text=row['text'],
            risk_level=risk_enum,
            trigger_tags=trigger_tags,
            applicable_routes=applicable_routes,
            target_gender=row['target_gender'] if 'target_gender' in row.keys() else None,
            age_min=row['age_min'] if 'age_min' in row.keys() else None,
            age_max=row['age_max'] if 'age_max' in row.keys() else None,
            requires_other_meds=bool(row['requires_other_meds']) if 'requires_other_meds' in row.keys() else False
        )

    def get_questions_by_ids(self, question_ids: List[str]) -> List[Question]:
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
            
            questions = [self._map_row_to_question(row) for row in rows]
            
            conn.close()
            return questions
            
        except Exception as e:
            logger.error(f"Erreur get_questions_by_ids: {e}", exc_info=True)
            return []
    
    def get_substance_tags(self, identifier: str) -> List[str]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            import json
            
            cursor.execute("SELECT tags FROM substances WHERE code = ?", (identifier,))
            row = cursor.fetchone()
            
            if row and row['tags']:
                conn.close()
                return json.loads(row['tags']) if isinstance(row['tags'], str) else row['tags']

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
            logger.error(f"Erreur get_substance_tags: {e}", exc_info=True)
            return []
    
    def get_questions_by_tags(self, tags: List[str]) -> List[Question]:
        if not tags:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM questions")
            rows = cursor.fetchall()
            
            questions = []
            for row in rows:
                question = self._map_row_to_question(row)
                
                if any(tag in tags for tag in question.trigger_tags):
                    questions.append(question)
            
            conn.close()
            return questions
            
        except Exception as e:
            logger.error(f"Erreur get_questions_by_tags: {e}", exc_info=True)
            return []
    
    def get_drug_route(self, cis: str) -> Optional[str]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT administration_route FROM drugs WHERE cis = ?", (cis,))
            row = cursor.fetchone()
            
            conn.close()
            return row['administration_route'] if row else None
            
        except Exception as e:
            logger.error(f"Erreur get_drug_route: {e}", exc_info=True)
            return None
