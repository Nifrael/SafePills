"""
Service de Recherche Simplifié (KISS)
Recherche dans la table 'drugs' et 'substances' SQLite.
"""
import sqlite3
import os
import unicodedata
import logging
from typing import List
from ..core.schemas import SearchResult
from ..core.models import Drug, Substance

logger = logging.getLogger(__name__)

# Chemin DB (à centraliser idéalement)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'safepills.db')

def normalize_text(text: str) -> str:
    """Retire accents et met en minuscules pour la recherche"""
    if not text: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn').lower()

def search_medication(query: str) -> List[SearchResult]:
    """
    Recherche médicaments ET substances correspondant à la requête
    """
    clean_query = normalize_text(query)
    if len(clean_query) < 2:
        return []

    results = []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Recherche Substances
        # On cherche les substances qui matchent
        cursor.execute(
            "SELECT code, name FROM substances"
        )
        
        # Filtrage Python (plus simple pour les accents avec SQLite par défaut)
        # Mais pour la perf, on fera du SQL LIKE plus tard si besoin
        # Ici on charge tout (133 substances c'est rien) et on filtre
        all_subs = cursor.fetchall()
        for sub in all_subs:
            if clean_query in normalize_text(sub['name']):
                results.append(SearchResult(
                    type="substance",
                    id=sub['code'],
                    name=sub['name'],
                    description="Substance active"
                ))
        
        # 2. Recherche Médicaments OTC
        cursor.execute(
            "SELECT cis, name FROM drugs WHERE is_otc = 1"
        )
        all_drugs = cursor.fetchall()
        for drug in all_drugs:
            if clean_query in normalize_text(drug['name']):
                results.append(SearchResult(
                    type="drug",
                    id=drug['cis'],
                    name=drug['name'],
                    description="Médicament"
                ))
                
        conn.close()
        
    except Exception as e:
        logger.error(f"Erreur recherche SQLite: {e}", exc_info=True)
        return []
        
    return results[:20] # Limite à 20 résultats

def get_drug_details(cis: str) -> Drug:
    """Récupère un médicament et ses substances"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Info Drug
        cursor.execute("SELECT * FROM drugs WHERE cis = ?", (cis,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
            
        drug = Drug(
            cis=row['cis'],
            name=row['name'],
            administration_route=row['administration_route'],
            is_otc=bool(row['is_otc']),
            substances=[]
        )
        
        # Info Substances liées
        cursor.execute("""
            SELECT s.code, s.name, s.tags 
            FROM substances s
            JOIN drug_substances ds ON s.code = ds.substance_code
            WHERE ds.drug_cis = ?
        """, (cis,))
        
        sub_rows = cursor.fetchall()
        import json
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
            
        conn.close()
        return drug
        
    except Exception as e:
        logger.error(f"Erreur détails drug: {e}", exc_info=True)
        return None
