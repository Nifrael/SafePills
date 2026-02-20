import sqlite3
import logging
import json
from typing import List, Optional, Tuple
from backend.core.config import settings
from backend.core.schemas import SearchResult
from backend.core.models import Brand, Substance

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
                cursor.execute("SELECT id, name FROM substances")
                all_subs = cursor.fetchall()
                
                from backend.services.search.utils import normalize_text
                
                for sub in all_subs:
                    if normalized_query in normalize_text(sub['name']):
                        results.append(SearchResult(
                            type="substance",
                            id=str(sub['id']),
                            name=sub['name'],
                            description=i18n.get("type_substance", lang, "search") or "Substance active"
                        ))
        except Exception as e:
            logger.error(f"Error searching substances: {e}", exc_info=True)
            
        return results

    def search_drugs(self, normalized_query: str, lang: str = "fr") -> List[SearchResult]:
        from backend.core.i18n import i18n
        from backend.services.search.utils import normalize_text
        results = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT cis, name, is_otc FROM brands")
                all_drugs = cursor.fetchall()
                
                for drug in all_drugs:
                    if normalized_query in normalize_text(drug['name']):
                        is_otc = bool(drug['is_otc'])
                        if is_otc:
                            desc = i18n.get("type_drug", lang, "search") or "Médicament (Accès libre)"
                        else:
                            desc = i18n.get("type_drug_prescription", lang, "search") or "💊 Sous prescription médicale"
                            
                        results.append(SearchResult(
                            type="drug",
                            id=drug['cis'],
                            name=drug['name'],
                            description=desc
                        ))
        except Exception as e:
            logger.error(f"Error searching drugs: {e}", exc_info=True)
            
        return results

    def get_drug_details(self, cis: str) -> Optional[dict]:
        from backend.core.models import Brand, BrandSubstance, Substance as MetierSubstance
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM brands WHERE cis = ?", (cis,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                brand = Brand(
                    id=row['id'],
                    cis=row['cis'],
                    name=row['name'],
                    administration_route=row['administration_route'],
                    is_otc=bool(row['is_otc']),
                    composition=[]
                )

                cursor.execute("""
                    SELECT s.id, s.name, bs.dosage
                    FROM substances s
                    JOIN brand_substances bs ON s.id = bs.substance_id
                    WHERE bs.brand_id = ?
                """, (brand.id,))
                
                sub_rows = cursor.fetchall()
                for s_row in sub_rows:
                    sub_model = MetierSubstance(
                        id=s_row['id'],
                        name=s_row['name']
                    )
                    br_sub = BrandSubstance(
                        substance=sub_model,
                        dosage=s_row['dosage']
                    )
                    brand.composition.append(br_sub)
                
                return brand
                
        except Exception as e:
            logger.error(f"Error retrieving brand details for {cis}: {e}", exc_info=True)
            return None
