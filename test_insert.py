import sqlite3, json
with open("backend/data/medical_knowledge.json", "r") as f:
    med_knowledge = json.load(f)

conn = sqlite3.connect("backend/data/safepills.db")
cursor = conn.cursor()

from backend.scripts.update_rules import normalize_name

cursor.execute("SELECT id, name FROM families")
family_rows = cursor.fetchall()
family_ids = {row[1]: row[0] for row in family_rows}

cursor.execute("SELECT id, name FROM substances")
substance_rows = cursor.fetchall()
substance_ids = {row[1]: row[0] for row in substance_rows}

rules_data = med_knowledge.get('rules', {})
rules_inserted = 0

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
        
        try:
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
                int(rule.get('filter_polymedication', 0)),
                rule.get('filter_gender'),
                rule.get('age_min')
            ))
            rules_inserted += 1
        except Exception as e:
            print(f"FAILED TO INSERT {rule['question_code']} : {e}")

print("Total:", rules_inserted)
