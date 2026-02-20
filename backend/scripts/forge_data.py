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
    return n.lower().strip()

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

def forge_database():
    print("🚀 Début de la Forge SafePills...")
    
    with open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
        whitelist = json.load(f)
    
    allowed_routes = whitelist.get("allowed_routes", [])
    wl_families = whitelist.get("families", {})
    specific_brands = [normalize_name(b) for b in whitelist.get("specific_brands_allowed", [])]
    otc_overrides = whitelist.get("otc_overrides", {})
    otc_overrides_norm = {normalize_name(k): v for k, v in otc_overrides.items()}

    substance_to_families = {}
    for fam_name, subs in wl_families.items():
        for sub in subs:
            sub_norm = normalize_name(sub)
            if sub_norm not in substance_to_families:
                substance_to_families[sub_norm] = []
            substance_to_families[sub_norm].append(fam_name)

    otc_names = load_otc_names()

    print("📖 Lecture CIS_bdpm.txt...")
    cis_info = {} # cis -> {name, route}
    try:
        with open(CIS_PATH, 'r', encoding='latin-1') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    cis = parts[0]
                    name = parts[1].strip()
                    route = parts[3].lower()
                    
                    if any(r in route for r in allowed_routes):
                        cis_info[cis] = {
                            "name": name,
                            "route": route,
                            "norm_name": normalize_name(name)
                        }
    except Exception as e:
         print(f"❌ Erreur lecture CIS: {e}")
         return

    print("🧪 Lecture CIS_COMPO_bdpm.txt...")
    brands_to_import = {} # cis -> dict details
    substances_to_import = set()
    
    try:
        with open(COMPO_PATH, 'r', encoding='latin-1') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 6:
                    cis = parts[0]
                    if cis not in cis_info:
                        continue 
                    
                    substance_name = parts[3].strip()
                    dosage = parts[4].strip() + " " + parts[5].strip()
                    sub_norm = normalize_name(substance_name)
                    
                    brand_info = cis_info[cis]
                    norm_brand_name = brand_info['norm_name']
                    
                    is_substance_allowed = sub_norm in substance_to_families
                    is_brand_vip = any(vip in norm_brand_name for vip in specific_brands)
                    
                    if is_substance_allowed or is_brand_vip:
                        if cis not in brands_to_import:
                            is_otc = any(otc in norm_brand_name for otc in otc_names)
                            
                            for ov_key, ov_val in otc_overrides_norm.items():
                                if ov_key in norm_brand_name or ov_key in sub_norm:
                                    is_otc = ov_val
                                    break
                            
                            brands_to_import[cis] = {
                                "cis": cis,
                                "name": brand_info["name"],
                                "route": brand_info["route"],
                                "is_otc": is_otc,
                                "composition": []
                            }
                        
                        brands_to_import[cis]["composition"].append({
                            "substance": substance_name,
                            "norm_substance": sub_norm,
                            "dosage": dosage
                        })
                        substances_to_import.add(substance_name)
    except Exception as e:
        print(f"❌ Erreur lecture COMPO: {e}")
        return

    print(f"✅ Filtrage terminé. Marques à importer : {len(brands_to_import)}")
    
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
        if norm_sub in substance_to_families:
            for fam_name in substance_to_families[norm_sub]:
                fam_id = family_ids.get(fam_name)
                if fam_id:
                    cursor.execute("INSERT INTO substance_families (substance_id, family_id) VALUES (?, ?)", (sub_id, fam_id))

    for cis, brand in brands_to_import.items():
        cursor.execute(
            "INSERT INTO brands (cis, name, administration_route, is_otc) VALUES (?, ?, ?, ?)",
            (brand['cis'], brand['name'], brand['route'], brand['is_otc'])
        )
        brand_id = cursor.lastrowid
        
        for compo in brand['composition']:
            sub_id = substance_ids[compo['substance']]
            cursor.execute(
                "INSERT INTO brand_substances (brand_id, substance_id, dosage) VALUES (?, ?, ?)",
                (brand_id, sub_id, compo['dosage'])
            )

    conn.commit()

    print("📚 Importation des Règles Médicales (Medical Knowledge)...")
    MED_KNOWLEDGE_PATH = os.path.join(DATA_DIR, 'medical_knowledge.json')
    try:
        with open(MED_KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
            med_knowledge = json.load(f)
            
        rules_inserted = 0
        for rule in med_knowledge.get('rules', []):
            family_id = None
            if 'target_family' in rule:
                fam_name = rule['target_family']
                family_id = family_ids.get(fam_name)
                if not family_id:
                    print(f"⚠️ Famille '{fam_name}' inconnue pour la règle {rule['question_code']}. Ignorée.")
                    continue
                    
            substance_id = None
            if 'target_substance' in rule:
                sub_norm = normalize_name(rule['target_substance'])
                for s_name, s_id in substance_ids.items():
                    if normalize_name(s_name) == sub_norm:
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
    forge_database()
