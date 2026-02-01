"""
Script d'Import JSON -> SQLite
Charge le fichier `pharma_data.json` dans la base de données SQLite `safepills.db`.
"""
import json
import sqlite3
import os
import sys

# Chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
JSON_PATH = os.path.join(DATA_DIR, 'pharma_data.json')
DB_PATH = os.path.join(DATA_DIR, 'safepills.db')

def init_db(cursor):
    """Crée les tables si elles n'existent pas (Schéma Minimaliste)"""
    cursor.executescript("""
        PRAGMA foreign_keys = ON;
        
        CREATE TABLE IF NOT EXISTS drugs (
            cis TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            administration_route TEXT,
            is_otc BOOLEAN DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS substances (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            tags TEXT DEFAULT '[]'
        );
        
        CREATE TABLE IF NOT EXISTS drug_substances (
            drug_cis TEXT NOT NULL,
            substance_code TEXT NOT NULL,
            dosage TEXT,
            PRIMARY KEY (drug_cis, substance_code),
            FOREIGN KEY(drug_cis) REFERENCES drugs(cis),
            FOREIGN KEY(substance_code) REFERENCES substances(code)
        );
        
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            text TEXT NOT NULL,
            trigger_tags TEXT NOT NULL,
            risk_level TEXT NOT NULL
        );
    """)

def import_data():
    if not os.path.exists(JSON_PATH):
        print(f"❌ Fichier introuvable : {JSON_PATH}")
        sys.exit(1)
        
    print(f"📖 Lecture de {JSON_PATH}...")
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Initialisation du schéma si nécessaire
    init_db(cursor)
    
    print("🧹 Nettoyage des anciennes données...")
    cursor.executescript("""
        DELETE FROM drug_substances;
        DELETE FROM drugs;
        DELETE FROM substances;
        -- On ne supprime pas les questions si elles ont été entrées manuellement ailleurs
    """)
    
    # 1. Import Substances
    print(f"💉 Importation de {len(data['substances'])} substances...")
    for sub in data['substances']:
        cursor.execute(
            "INSERT INTO substances (code, name, tags) VALUES (?, ?, ?)",
            (sub['name'], sub['name'], json.dumps(sub['tags'])) # Code = Nom pour simplifier ici
        )
        
    # 2. Import Drugs & Liens
    print(f"💊 Importation de {len(data['drugs'])} médicaments...")
    link_count = 0
    for drug in data['drugs']:
        # Drug
        cursor.execute(
            "INSERT INTO drugs (cis, name, administration_route, is_otc) VALUES (?, ?, ?, ?)",
            (drug['cis'], drug['name'], drug['admin_route'], drug['is_otc'])
        )
        
        # Liens Substances
        for sub_name in drug['substances']:
            # On vérifie que la substance existe (par sécurité)
            cursor.execute("INSERT OR IGNORE INTO drug_substances (drug_cis, substance_code) VALUES (?, ?)", 
                           (drug['cis'], sub_name))
            link_count += 1
            
    # 3. Import Questions (si présentes dans le JSON)
    if 'questions' in data and data['questions']:
        print(f"❓ Importation de {len(data['questions'])} questions...")
        for q in data['questions']:
            cursor.execute(
                "INSERT OR REPLACE INTO questions (id, text, trigger_tags, risk_level) VALUES (?, ?, ?, ?)",
                (q['id'], q['text'], json.dumps(q['trigger_tags']), q['risk_level'])
            )

    conn.commit()
    conn.close()
    
    print("✨ Import terminé avec succès !")
    print(f"   - {len(data['drugs'])} médicaments")
    print(f"   - {len(data['substances'])} substances")
    print(f"   - {link_count} liens créés")

if __name__ == "__main__":
    import_data()
