import os
import sqlite3
import json
import pandas as pd
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
SCRIPTS_DATA_DIR = os.path.join(BASE_DIR, '..', '..', 'scripts_data')

DB_PATH = os.path.join(DATA_DIR, 'safepills.db')
WHITELIST_PATH = os.path.join(DATA_DIR, 'whitelist.json')
OTC_PATH = os.path.join(SCRIPTS_DATA_DIR, 'Liste-OTC.xls')
CIS_PATH = os.path.join(SCRIPTS_DATA_DIR, 'CIS_bdpm.txt')
COMPO_PATH = os.path.join(SCRIPTS_DATA_DIR, 'CIS_COMPO_bdpm.txt')

def init_db(cursor):
    cursor.executescript("""
        PRAGMA foreign_keys = OFF;
        
        -- Drop old schema
        DROP TABLE IF EXISTS drug_substances;
        DROP TABLE IF EXISTS drugs;
        DROP TABLE IF EXISTS questions;
        
        -- Drop new schema
        DROP TABLE IF EXISTS rules;
        DROP TABLE IF EXISTS substance_families;
        DROP TABLE IF EXISTS brand_substances;
        DROP TABLE IF EXISTS brands;
        DROP TABLE IF EXISTS substances;
        DROP TABLE IF EXISTS families;

        PRAGMA foreign_keys = ON;

        CREATE TABLE families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE substances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE substance_families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            substance_id INTEGER NOT NULL,
            family_id INTEGER NOT NULL,
            FOREIGN KEY(substance_id) REFERENCES substances(id),
            FOREIGN KEY(family_id) REFERENCES families(id)
        );

        CREATE TABLE brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cis TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            administration_route TEXT,
            is_otc BOOLEAN DEFAULT 0
        );

        CREATE TABLE brand_substances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_id INTEGER NOT NULL,
            substance_id INTEGER NOT NULL,
            dosage TEXT,
            FOREIGN KEY(brand_id) REFERENCES brands(id),
            FOREIGN KEY(substance_id) REFERENCES substances(id)
        );

        CREATE TABLE rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_code TEXT NOT NULL,
            risk_level INTEGER NOT NULL, -- 1=SAFE, 2=CAUTION, 3=AVOID, 4=CONTRAINDICATED
            advice TEXT NOT NULL,
            family_id INTEGER,
            substance_id INTEGER,
            filter_route TEXT,
            filter_polymedication BOOLEAN DEFAULT 0,
            filter_gender TEXT,
            age_min INTEGER,
            FOREIGN KEY(family_id) REFERENCES families(id),
            FOREIGN KEY(substance_id) REFERENCES substances(id)
        );
    """)

def normalize_name(name):
    import unicodedata
    if not isinstance(name, str):
        return ""
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    n = n.lower().strip()
    n = n.replace('-', '')
    return n

def load_otc_names():
    otc_names = set()
    try:
        df = pd.read_excel(OTC_PATH, header=2)
        for val in df['Nom du médicament'].dropna():
            base_name = str(val).split(',')[0].strip()
            otc_names.add(normalize_name(base_name))
        print(f"📦 {len(otc_names)} noms OTC chargés.")
    except Exception as e:
        print(f"❌ Erreur lecture OTC : {e}")
    return otc_names

def build_database():
    print("🚀 Début de l'intégration dans SafePills (SQLite)...")
    
    PHARMA_DATA_PATH = os.path.join(DATA_DIR, 'pharma_data.json')
    if not os.path.exists(PHARMA_DATA_PATH):
        print(f"❌ Fichier manquant: {PHARMA_DATA_PATH}. Veuillez lancer extract_data.py d'abord.")
        return
        
    try:
        with open(PHARMA_DATA_PATH, 'r', encoding='utf-8') as f:
            pharma_data = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lecture de la donnée JSON : {e}")
        return
        
    wl_families = pharma_data.get("families", {})
    substances_to_import = pharma_data.get("substances", [])
    brands_to_import = pharma_data.get("brands", [])
    substance_to_families = pharma_data.get("substance_to_families", {})

    print("💾 Insertion dans SQLite...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    init_db(cursor)

    family_ids = {} 
    for fam_name in wl_families.keys():
        cursor.execute("INSERT INTO families (name) VALUES (?)", (fam_name,))
        family_ids[fam_name] = cursor.lastrowid

    substance_ids = {} 
    for sub_name in substances_to_import:
        cursor.execute("INSERT INTO substances (name) VALUES (?)", (sub_name,))
        sub_id = cursor.lastrowid
        substance_ids[sub_name] = sub_id
        
        norm_sub = normalize_name(sub_name)
        for known_sub, fams in substance_to_families.items():
            if known_sub in norm_sub:
                for fam_name in fams:
                    fam_id = family_ids.get(fam_name)
                    if fam_id:
                        cursor.execute("INSERT INTO substance_families (substance_id, family_id) VALUES (?, ?)", (sub_id, fam_id))

    for brand in brands_to_import:
        cursor.execute(
            "INSERT INTO brands (cis, name, administration_route, is_otc) VALUES (?, ?, ?, ?)",
            (brand['cis'], brand['name'], brand['route'], brand['is_otc'])
        )
        brand_id = cursor.lastrowid
        
        for compo in brand['composition']:
            sub_id = substance_ids.get(compo['substance'])
            if sub_id:
                cursor.execute(
                    "INSERT INTO brand_substances (brand_id, substance_id, dosage) VALUES (?, ?, ?)",
                    (brand_id, sub_id, compo.get('dosage'))
                )

    conn.commit()

    print("📚 Importation des Règles Médicales (Medical Knowledge)...")
    MED_KNOWLEDGE_PATH = os.path.join(DATA_DIR, 'medical_knowledge.json')
    try:
        with open(MED_KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
            med_knowledge = json.load(f)
            
        rules_inserted = 0
        rules_data = med_knowledge.get('rules', {})
        
        for fam_name, rules_list in rules_data.items():
            for rule in rules_list:
                family_id = None
                if fam_name != "GLOBAL":
                    family_id = family_ids.get(fam_name)
                    if not family_id:
                        print(f"⚠️ Famille '{fam_name}' inconnue pour la règle {rule['question_code']}. Ignorée.")
                        continue
                        
                substance_id = None
                if 'target_substance' in rule:
                    sub_norm = normalize_name(rule['target_substance'])
                    for s_name, s_id in substance_ids.items():
                        if sub_norm in normalize_name(s_name):
                            substance_id = s_id
                            break
                    
                    if not substance_id:
                        print(f"⚠️ Substance '{rule['target_substance']}' inconnue pour la règle {rule['question_code']}. Ignorée.")
                        continue

                cursor.execute("""
                    INSERT INTO rules (
                        question_code, risk_level, advice, family_id, substance_id,
                        filter_route, filter_polymedication, filter_gender, age_min
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule['question_code'],
                    rule['risk_level'],
                    rule['advice'],
                    family_id,
                    substance_id,
                    rule.get('filter_route'),
                    rule.get('filter_polymedication', 0),
                    rule.get('filter_gender'),
                    rule.get('age_min')
                ))
                rules_inserted += 1
            
        conn.commit()
        print(f"✅ {rules_inserted} règles insérées avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors de l'import des règles : {e}")

    conn.close()
    print("✨ Base de données générée avec succès (Schéma Relationnel Majeur).")

if __name__ == "__main__":
    build_database()
