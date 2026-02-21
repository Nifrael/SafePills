import sqlite3
import logging
from typing import List, Optional
from backend.core.config import settings
from backend.core.schemas import SearchResult
from backend.core.models import Brand, BrandSubstance, Substance as MetierSubstance
from backend.core.i18n import i18n

logger = logging.getLogger(__name__)


class DrugRepository:
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DB_PATH

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def search_substances(self, normalized_query: str, lang: str = "fr") -> List[SearchResult]:
        results = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name FROM substances WHERE LOWER(name) LIKE ? LIMIT 20",
                    (f"%{normalized_query}%",)
                )
                
                desc = i18n.get("type_substance", lang, "search") or "Substance active"
                for sub in cursor.fetchall():
                    results.append(SearchResult(
                        type="substance",
                        id=str(sub['id']),
                        name=sub['name'],
                        description=desc
                    ))
        except Exception as e:
            logger.error(f"Erreur recherche substances: {e}", exc_info=True)
            
        return results

    def search_drugs(self, normalized_query: str, lang: str = "fr") -> List[SearchResult]:
        """Recherche les médicaments (marques) via SQL LIKE (délégation au moteur DB)."""
        results = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT cis, name, is_otc FROM brands WHERE LOWER(name) LIKE ? LIMIT 20",
                    (f"%{normalized_query}%",)
                )
                
                desc = i18n.get("type_drug", lang, "search") or "Médicament"
                for drug in cursor.fetchall():
                    results.append(SearchResult(
                        type="drug",
                        id=drug['cis'],
                        name=drug['name'],
                        description=desc
                    ))
        except Exception as e:
            logger.error(f"Erreur recherche médicaments: {e}", exc_info=True)
            
        return results

    def get_drug_details(self, cis: str) -> Optional[Brand]:
        """Récupère les détails complets d'un médicament par son code CIS."""
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
                
                for s_row in cursor.fetchall():
                    sub_model = MetierSubstance(
                        id=s_row['id'],
                        name=s_row['name']
                    )
                    brand.composition.append(BrandSubstance(
                        substance=sub_model,
                        dosage=s_row['dosage']
                    ))
                
                return brand
                
        except Exception as e:
            logger.error(f"Erreur détails médicament {cis}: {e}", exc_info=True)
            return None
