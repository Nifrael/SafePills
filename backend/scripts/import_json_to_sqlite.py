"""
Script d'Import JSON -> SQLite
Charge le fichier `pharma_data.json` dans la base de données SQLite `safepills.db`.
Fusionne avec `medical_knowledge.json` (Nouvelle Structure Profils).
"""
import json
import sqlite3
import os
import sys

# Chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
JSON_PATH = os.path.join(DATA_DIR, 'pharma_data.json')
KNOWLEDGE_PATH = os.path.join(DATA_DIR, 'medical_knowledge.json')
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
            risk_level TEXT NOT NULL,
            applicable_routes TEXT DEFAULT '[]',
            target_gender TEXT,
            age_min INTEGER,
            age_max INTEGER,
            requires_other_meds BOOLEAN DEFAULT 0
        );
    """)

def import_data():
    # ... (Loading files remains same) ...
    # 1. Chargement Drugs (Brut)
    if not os.path.exists(JSON_PATH):
        print(f"❌ Fichier Drugs introuvable : {JSON_PATH}")
        sys.exit(1)
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        drugs_data = json.load(f)

    # 2. Chargement Knowledge (Nouvelle Structure)
    knowledge = {}
    if os.path.exists(KNOWLEDGE_PATH):
        print(f"🧠 Lecture de {KNOWLEDGE_PATH}...")
        with open(KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
            knowledge = json.load(f)
    else:
        print("⚠️ Pas de fichier medical_knowledge.json. Création d'une base vide.")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    init_db(cursor)
    
    # Auto-Migration
    try: cursor.execute("ALTER TABLE questions ADD COLUMN applicable_routes TEXT DEFAULT '[]'")
    except: pass
    try: cursor.execute("ALTER TABLE questions ADD COLUMN target_gender TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE questions ADD COLUMN age_min INTEGER")
    except: pass
    try: cursor.execute("ALTER TABLE questions ADD COLUMN age_max INTEGER")
    except: pass
    try: cursor.execute("ALTER TABLE questions ADD COLUMN requires_other_meds BOOLEAN DEFAULT 0")
    except: pass

    print("🧹 Nettoyage...")
    cursor.executescript("DELETE FROM drug_substances; DELETE FROM drugs; DELETE FROM substances; DELETE FROM questions;")

    # --- PROCESSING INTELLIGENT ---
    
    substances_tags_map = {} 
    questions_to_insert = {} 

    catalog = knowledge.get('questions_catalog', {})
    profiles = knowledge.get('risk_profiles', {})
    classification = knowledge.get('substances_classification', {})

    # A. On parcourt la classification
    for sub_name, sub_profiles in classification.items():
        if sub_name not in substances_tags_map:
            substances_tags_map[sub_name] = set()

        for profile_name in sub_profiles:
            profile = profiles.get(profile_name)
            if not profile:
                continue
                
            for rule in profile: 
                q_id_base = rule['id']
                risk = rule['risk']
                routes = rule.get('routes', [])
                gender = rule.get('gender', None)
                age_min = rule.get('age_min', None)
                age_max = rule.get('age_max', None)
                requires_other_meds = rule.get('requires_other_meds', False)  # NEW: Boolean simplification
                
                if q_id_base not in catalog: continue
                
                # ID Unique : La variante dépend aussi du genre maintenant !
                # Ex: Q_GROSSESSE_RED_F
                gender_suffix = f"_{gender}" if gender else ""
                q_variant_id = f"{q_id_base}_{risk}{gender_suffix}"
                
                trigger_tag = f"TRIGGER_{q_variant_id}"
                
                substances_tags_map[sub_name].add(trigger_tag)
                
                if q_variant_id not in questions_to_insert:
                    questions_to_insert[q_variant_id] = {
                        "text": catalog[q_id_base],
                        "risk": risk,
                        "trigger_tags": set(),
                        "routes": set(),
                        "gender": gender,
                        "age_min": age_min,
                        "age_max": age_max,
                        "requires_other_meds": requires_other_meds
                    }
                
                questions_to_insert[q_variant_id]["trigger_tags"].add(trigger_tag)
                for r in routes:
                    questions_to_insert[q_variant_id]["routes"].add(r)


    # --- IMPORT EN BASE ---

    # 1. Substances
    print(f"💉 Traitement des substances...")
    for sub in drugs_data['substances']:
        name = sub['name']
        tags = list(substances_tags_map.get(name, []))
        
        cursor.execute(
            "INSERT INTO substances (code, name, tags) VALUES (?, ?, ?)",
            (name, name, json.dumps(tags))
        )

    # 2. Questions
    print(f"❓ Création des {len(questions_to_insert)} questions configurées...")
    for q_var_id, data in questions_to_insert.items():
        cursor.execute(
            "INSERT INTO questions (id, text, trigger_tags, risk_level, applicable_routes, target_gender, age_min, age_max, requires_other_meds) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                q_var_id, 
                data['text'], 
                json.dumps(list(data['trigger_tags'])), 
                data['risk'], 
                json.dumps(list(data['routes'])),
                data['gender'],
                data['age_min'],
                data['age_max'],
                data['requires_other_meds']
            )
        )

    # 3. Médicaments
    print(f"💊 Importation des médicaments...")
    link_count = 0
    for drug in drugs_data['drugs']:
        cursor.execute(
            "INSERT INTO drugs (cis, name, administration_route, is_otc) VALUES (?, ?, ?, ?)",
            (drug['cis'], drug['name'], drug['admin_route'], drug['is_otc'])
        )
        for sub_name in drug['substances']:
            cursor.execute("INSERT OR IGNORE INTO drug_substances (drug_cis, substance_code) VALUES (?, ?)", 
                           (drug['cis'], sub_name))
            link_count += 1

    conn.commit()
    conn.close()
    
    print("✨ Import terminé avec succès (Mode Profils) !")
    print(f"   - {len(substances_tags_map)} substances configurées avec risque.")

if __name__ == "__main__":
    import_data()
