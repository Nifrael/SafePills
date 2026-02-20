import json

def format_rules():
    path = "backend/data/medical_knowledge.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data.get("rules"), list):
        new_rules = {}
        for rule in data["rules"]:
            family = rule.pop("target_family", "GLOBAL")
            
            if family not in new_rules:
                new_rules[family] = []
                
            new_rules[family].append(rule)
            
        data["rules"] = new_rules
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    format_rules()
