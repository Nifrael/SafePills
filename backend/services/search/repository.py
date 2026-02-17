import sqlite3
import logging
import json
from typing import List, Optional, Tuple
from backend.core.config import settings
from backend.core.schemas import SearchResult
from backend.core.models import Drug, Substance

logger = logging.getLogger(__name__)

class DrugRepository:
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def search_substances(self, normalized_query: str, lang: str = "fr") -> List[SearchResult]:
        from backend.core.i18n import i18n
        results = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT code, name FROM substances")
                all_subs = cursor.fetchall()
                
                from backend.services.search.utils import normalize_text
                
                for sub in all_subs:
                    if normalized_query in normalize_text(sub['name']):
                        results.append(SearchResult(
                            type="substance",
                            id=sub['code'],
                            name=sub['name'],
                            description=i18n.get("type_substance", lang, "search") or "Substance active"
                        ))
        except Exception as e:
            logger.error(f"Error searching substances: {e}", exc_info=True)
            
        return results

    def search_drugs(self, normalized_query: str, lang: str = "fr") -> List[SearchResult]:
        from backend.core.i18n import i18n
        results = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT cis, name FROM drugs WHERE is_otc = 1")
                all_drugs = cursor.fetchall()
                
                from backend.services.search.utils import normalize_text
                
                for drug in all_drugs:
                    if normalized_query in normalize_text(drug['name']):
                        results.append(SearchResult(
                            type="drug",
                            id=drug['cis'],
                            name=drug['name'],
                            description=i18n.get("type_drug", lang, "search") or "Médicament"
                        ))
        except Exception as e:
            logger.error(f"Error searching drugs: {e}", exc_info=True)
            
        return results

    def get_drug_details(self, cis: str) -> Optional[Drug]:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM drugs WHERE cis = ?", (cis,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                drug = Drug(
                    cis=row['cis'],
                    name=row['name'],
                    administration_route=row['administration_route'],
                    is_otc=bool(row['is_otc']),
                    substances=[]
                )

                cursor.execute("""
                    SELECT s.code, s.name, s.tags 
                    FROM substances s
                    JOIN drug_substances ds ON s.code = ds.substance_code
                    WHERE ds.drug_cis = ?
                """, (cis,))
                
                sub_rows = cursor.fetchall()
                for s_row in sub_rows:
                    tags = []
                    if s_row['tags']:
                        try:
                            tags = json.loads(s_row['tags'])
                        except:
                            pass
                    
                    drug.substances.append(Substance(
                        code=s_row['code'],
                        name=s_row['name'],
                        tags=tags
                    ))
                
                return drug
                
        except Exception as e:
            logger.error(f"Error retrieving drug details for {cis}: {e}", exc_info=True)
            return None
