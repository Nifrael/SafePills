import unicodedata
from typing import List, Dict
from backend.services.drug_loader import load_drugs
from backend.core.models import Drug

def normalize_string(s: str) -> str:
    """Enlève les accents et met en majuscules pour une recherche robuste."""
    if not s:
        return ""
    # Normalise les caractères (ex: É -> E)
    s = unicodedata.normalize('NFD', s)
    s = "".join([c for c in s if unicodedata.category(c) != 'Mn'])
    return s.upper().strip()

class SearchEngine:
    def __init__(self, data_dir: str):
        """Initialise le moteur et pré-calcule les index de recherche."""
        self.drugs = load_drugs(data_dir)
        # Index pour la recherche par substance : {nom_normalise: [liste_de_drugs]}
        self.substance_index: Dict[str, List[Drug]] = {}
        self._build_indexes()

    def _build_indexes(self):
        """Construit les index pour accélérer la recherche."""
        for drug in self.drugs:
            for sub in drug.substances:
                # On utilise le nom normalisé pour l'index
                sub_name_norm = normalize_string(sub.nom)
                if sub_name_norm not in self.substance_index:
                    self.substance_index[sub_name_norm] = []
                self.substance_index[sub_name_norm].append(drug)

    def search(self, query: str) -> List[Drug]:
        """
        Recherche optimisée et insensible aux accents.
        """
        if not query:
            return []

        query_norm = normalize_string(query)
        results_map = {}

        # 1. Recherche dans les noms de marques (Marque)
        for drug in self.drugs:
            if query_norm in normalize_string(drug.nom):
                results_map[drug.cis] = drug

        # 2. Recherche dans l'index des substances
        for sub_name_norm, associated_drugs in self.substance_index.items():
            if query_norm in sub_name_norm:
                for drug in associated_drugs:
                    results_map[drug.cis] = drug
        
        return list(results_map.values())
