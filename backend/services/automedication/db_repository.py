import sqlite3
import logging
from typing import List, Optional
from backend.core.models import Rule, RiskLevel
from backend.core.config import settings

logger = logging.getLogger(__name__)


class AutomedicationRepository:
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _map_row_to_rule(self, row) -> Rule:
        try:
            risk_enum = RiskLevel(row['risk_level'])
        except ValueError:
            risk_enum = RiskLevel.LEVEL_1
        
        return Rule(
            id=row['id'],
            question_code=row['question_code'],
            risk_level=risk_enum,
            advice=row['advice'],
            family_id=row['family_id'],
            substance_id=row['substance_id'],
            filter_route=row['filter_route'],
            filter_polymedication=bool(row['filter_polymedication']),
            filter_gender=row['filter_gender'],
            age_min=row['age_min']
        )

    def get_rules_by_codes(self, question_codes: List[str]) -> List[Rule]:
        if not question_codes:
            return []
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                placeholders = ','.join('?' * len(question_codes))
                query = f"SELECT * FROM rules WHERE question_code IN ({placeholders})"
                
                cursor.execute(query, question_codes)
                rows = cursor.fetchall()
                
                return [self._map_row_to_rule(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Erreur get_rules_by_codes: {e}", exc_info=True)
            return []
    
    def get_rules_for_brand(self, identifier: str) -> List[Rule]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                substance_ids = []
                
                if len(identifier) == 8 and identifier.isdigit():
                    cursor.execute("""
                        SELECT s.id 
                        FROM substances s
                        JOIN brand_substances bs ON s.id = bs.substance_id
                        JOIN brands b ON bs.brand_id = b.id
                        WHERE b.cis = ?
                    """, (identifier,))
                    substance_rows = cursor.fetchall()
                    substance_ids = [row['id'] for row in substance_rows]
                else:
                    cursor.execute("SELECT id FROM substances WHERE id = ?", (identifier,))
                    row = cursor.fetchone()
                    if row:
                        substance_ids = [row['id']]
                
                if not substance_ids:
                    return []
                    
                placeholders = ','.join('?' * len(substance_ids))
                cursor.execute(f"""
                    SELECT DISTINCT family_id 
                    FROM substance_families 
                    WHERE substance_id IN ({placeholders})
                """, substance_ids)
                family_rows = cursor.fetchall()
                family_ids = [row['family_id'] for row in family_rows]
                
                rules_query = """
                    SELECT * FROM rules
                    WHERE 
                        (substance_id IN ({sub_ph}))
                        OR 
                        (family_id IN ({fam_ph}))
                """
                
                sub_ph = placeholders
                fam_ph = ','.join('?' * len(family_ids)) if family_ids else 'NULL'
                
                params = []
                params.extend(substance_ids)
                if family_ids:
                    params.extend(family_ids)
                    
                final_query = rules_query.format(sub_ph=sub_ph, fam_ph=fam_ph)
                cursor.execute(final_query, params)
                
                rules_rows = cursor.fetchall()
                return [self._map_row_to_rule(row) for row in rules_rows]
            
        except Exception as e:
            logger.error(f"Erreur get_rules_for_brand: {e}", exc_info=True)
            return []
            
    def get_drug_route(self, identifier: str) -> Optional[str]:
        try:
            if len(identifier) < 8:
                return None 
                
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT administration_route FROM brands WHERE cis = ?", (identifier,))
                row = cursor.fetchone()
                
                return row['administration_route'] if row else None
            
        except Exception as e:
            logger.error(f"Erreur get_drug_route: {e}", exc_info=True)
            return None
