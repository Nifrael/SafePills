import os
import sqlite3
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'safepills.db')
MED_KNOWLEDGE_PATH = os.path.join(DATA_DIR, 'medical_knowledge.json')

def normalize_name(name):
    import unicodedata
    if not isinstance(name, str):
        return ""
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    n = n.lower().strip()
    n = n.replace('-', '')
    return n

def update_rules():
    print("🚀 Début de la mise à jour des Règles Médicales (Medical Knowledge)...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données introuvable : {DB_PATH}. Veuillez d'abord lancer build_db.py.")
        return

    try:
        with open(MED_KNOWLEDGE_PATH, 'r', encoding='utf-8') as f:
            med_knowledge = json.load(f)
    except Exception as e:
        print(f"❌ Erreur lecture de medical_knowledge.json : {e}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM rules;")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='rules';")
    
    cursor.execute("SELECT id, name FROM families")
    family_rows = cursor.fetchall()
    family_ids = {row[1]: row[0] for row in family_rows}
    
    cursor.execute("SELECT id, name FROM substances")
    substance_rows = cursor.fetchall()
    substance_ids = {row[1]: row[0] for row in substance_rows}

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
    conn.close()
    
    print(f"✅ {rules_inserted} règles mises à jour avec succès dans SafePills.")

if __name__ == "__main__":
    update_rules()
