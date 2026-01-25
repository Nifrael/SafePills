import os

def explore_file(file_path, n_lines=5):
    print(f"\n--- Exploration de : {os.path.basename(file_path)} ---")
    if not os.path.exists(file_path):
        print(f"Erreur : Le fichier {file_path} est introuvable.")
        return

    try:
        # On essaie d'abord l'encodage classique des fichiers admin français
        with open(file_path, 'r', encoding='iso-8859-1') as f:
            for i in range(n_lines):
                line = f.readline()
                if not line:
                    break
                # On affiche la ligne brute (repr) pour voir les caractères invisibles comme \t
                print(f"Ligne {i+1} : {repr(line)}")
    except Exception as e:
        print(f"Erreur lors de la lecture : {e}")

if __name__ == "__main__":
    base_path = "backend/data/raw"
    explore_file(os.path.join(base_path, "CIS_bdpm.txt"))
    explore_file(os.path.join(base_path, "CIS_COMPO_bdpm.txt"))
