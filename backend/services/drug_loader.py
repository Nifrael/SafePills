import os
import sqlite3
import re
from typing import List, Dict
from backend.core.models import Drug, Substance, InteractionRule, SafePillsAnalysis

# Chemin vers la base de données SQLite (un simple fichier sur ton disque)
DB_PATH = "backend/safepills.db"

# Notre liste de test (MVP)
TARGET_DRUGS = [
    "DOLIPRANE", "CODOLIPRANE", "ADVIL", "KARDEGIC", "PREVISCAN", "XARELTO",
    "TAHOR", "CLAMOXYL", "AUGMENTIN", "SPASFON", "VENTOLINE",
    "LASILIX", "INEXIUM", "PLAVIX", "LEVOTHYROX", "MILLEPERTUIS"
]

def setup_database():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drugs (
            cis TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS substances (
            substance_code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            therapeutic_class TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drug_substances (
            drug_cis TEXT,
            substance_code TEXT,
            dose TEXT,
            FOREIGN KEY(drug_cis) REFERENCES drugs(cis),
            FOREIGN KEY(substance_code) REFERENCES substances(substance_code)
        )
    ''')
    conn.commit()
    return conn

def _simplify_name(full_name: str) -> str:
    """
    Simplifie le nom commercial pour faciliter la recherche utilisateur.
    """
    full_name_upper = full_name.upper()
    
    # On cherche si l'un de nos mots-clés est présent
    for target in sorted(TARGET_DRUGS, key=len, reverse=True):
        if target in full_name_upper:
            return target
            
    # Sinon, on prend le premier mot (souvent la marque)
    return re.split(r'[^a-zA-ZÀ-ÿ]', full_name)[0].upper()

def load_data_into_db(data_dir: str):
    """
    Lit les fichiers TXT de l'ANSM et injecte les données dans SQLite.
    """
    conn = setup_database()
    cursor = conn.cursor()
    
    cis_path = os.path.join(data_dir, "CIS_bdpm.txt")
    compo_path = os.path.join(data_dir, "CIS_COMPO_bdpm.txt")

    # 1. On traite d'abord les substances et les dosages
    with open(compo_path, 'r', encoding='iso-8859-1') as f:
        for line in f:
            cols = line.strip().split('\t')
            if len(cols) >= 4:
                cis, sub_code, sub_name, dose = cols[0], cols[2], cols[3], cols[4]
                
                # Insertion de la substance (on ignore si elle existe déjà)
                cursor.execute(
                    "INSERT OR IGNORE INTO substances (substance_code, name) VALUES (?, ?)", 
                    (sub_code, sub_name)
                )
                
                # Création du lien entre le médicament (CIS) et la substance
                cursor.execute(
                    "INSERT INTO drug_substances (drug_cis, substance_code, dose) VALUES (?, ?, ?)",
                    (cis, sub_code, dose)
                )

    # 2. On traite les noms de médicaments avec notre filtre MVP
    with open(cis_path, 'r', encoding='iso-8859-1') as f:
        for line in f:
            cols = line.strip().split('\t')
            if len(cols) >= 2:
                cis, full_name = cols[0], cols[1]
                
                # On ne garde que ce qui nous intéresse pour le TFM
                if any(target in full_name.upper() for target in TARGET_DRUGS):
                    clean_name = _simplify_name(full_name)
                    cursor.execute(
                        "INSERT OR IGNORE INTO drugs (cis, name) VALUES (?, ?)", 
                        (cis, clean_name)
                    )

    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès !")

if __name__ == "__main__":
    # On définit où se trouvent tes fichiers textes ANSM
    # Par défaut, on cherche un dossier 'data' à la racine
    DATA_DIRECTORY = "data/raw" 
    
    if os.path.exists(DATA_DIRECTORY):
        load_data_into_db(DATA_DIRECTORY)
    else:
        print(f"❌ Erreur : Le dossier '{DATA_DIRECTORY}' est introuvable.")