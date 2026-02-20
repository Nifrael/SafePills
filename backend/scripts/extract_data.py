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
    cis_info = {} 
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
    brands_to_import = {} 
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
                    is_substance_allowed = any(known_sub in sub_norm for known_sub in substance_to_families)
                    is_brand_vip = any(vip in norm_brand_name for vip in specific_brands)
                    
                    if is_substance_allowed or is_brand_vip:
                        if cis not in brands_to_import:
                            brands_to_import[cis] = {
                                "cis": cis,
                                "name": brand_info["name"],
                                "route": brand_info["route"],
                                "is_otc": False, 
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

    print(f"✅ Filtrage terminé. Marques brutes à importer : {len(brands_to_import)}")
    
    print("🚦 Application des règles et overrides OTC...")
    for brand in brands_to_import.values():
        norm_brand_name = normalize_name(brand["name"])
        is_otc = any(otc in norm_brand_name for otc in otc_names)
        
        has_true_override = False
        has_false_override = False
        
        for ov_key, ov_val in otc_overrides_norm.items():
            matches_brand_name = ov_key in norm_brand_name
            matches_any_substance = any(ov_key in c["norm_substance"] for c in brand["composition"])
            
            if matches_brand_name or matches_any_substance:
                if ov_val:
                    has_true_override = True
                else:
                    has_false_override = True
                    
        if has_false_override:
            brand["is_otc"] = False
        elif has_true_override:
            brand["is_otc"] = True
        else:
            brand["is_otc"] = is_otc
    
    print("🧹 Dé-duplication intelligente des génériques et marques...")
    grouped_brands = {}
    
    for brand in brands_to_import.values():
        norm_name = normalize_name(brand["name"])
        route = brand["route"]
        substances = [c["norm_substance"] for c in brand["composition"]]
        
        import re
        match = re.match(r"^([^\d,]+)", brand["name"])
        clean_name = match.group(1).strip().upper() if match else brand["name"].upper()
        
        is_generic = False
        for sub in sorted(substances, key=len, reverse=True):
            if norm_name.startswith(sub):
                is_generic = True
                clean_name = " + ".join(s.upper() for s in substances[:2])
                break
                
        group_key = (clean_name, route, frozenset(substances))
        
        if group_key not in grouped_brands:
            brand["name"] = f"{clean_name} ({route.capitalize()})"
            grouped_brands[group_key] = brand
        else:
            if brand["is_otc"]:
                grouped_brands[group_key]["is_otc"] = True

    final_brands = list(grouped_brands.values())
    print(f"📉 Après dé-duplication : {len(final_brands)} médicaments uniques conservés.")
    
    print("💾 Exportation au format JSON...")
    
    output_data = {
        "families": wl_families,
        "substances": list(substances_to_import),
        "brands": final_brands,
        "substance_to_families": substance_to_families
    }
    
    PHARMA_DATA_PATH = os.path.join(DATA_DIR, 'pharma_data.json')
    try:
        with open(PHARMA_DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"✨ Fichier {PHARMA_DATA_PATH} généré avec succès.")
    except Exception as e:
        print(f"❌ Erreur lors de la génération du JSON : {e}")

if __name__ == "__main__":
    forge_database()
