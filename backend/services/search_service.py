import sqlite3
from typing import List
from backend.core.models import Drug, Substance

DB_PATH = "backend/safepills.db"

def search_drugs(query: str) -> List[Drug]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()

    # On prépare le pattern de recherche
    search_pattern = f"%{query.upper()}%"

    # NOUVELLE REQUÊTE : 
    # On cherche dans 'drugs.name' OU dans 'substances.name'
    cursor.execute('''
        SELECT DISTINCT d.cis, d.name
        FROM drugs d
        LEFT JOIN drug_substances ds ON d.cis = ds.drug_cis
        LEFT JOIN substances s ON ds.substance_code = s.substance_code
        WHERE d.name LIKE ? OR s.name LIKE ?
        GROUP BY d.name
    ''', (search_pattern, search_pattern))

    drug_rows = cursor.fetchall()
    results = []

    for row in drug_rows:
        cis = row["cis"]
        # Pour chaque médicament trouvé, on récupère TOUTES ses substances
        cursor.execute('''
            SELECT s.substance_code, s.name, ds.dose 
            FROM substances s
            JOIN drug_substances ds ON s.substance_code = ds.substance_code
            WHERE ds.drug_cis = ?
        ''', (cis,))
        
        substance_rows = cursor.fetchall()
        substances = [
            Substance(
                substance_code=s["substance_code"],
                name=s["name"],
                dose=s["dose"]
            ) for s in substance_rows
        ]

        results.append(Drug(cis=cis, name=row["name"], substances=substances))

    conn.close()
    return results
