import pytest
from backend.services.search_service import SearchEngine

@pytest.fixture
def engine():
    # On initialise le moteur avec les données réelles (nos 120 médicaments)
    # Dans un vrai test unitaire on simulerait les données, mais ici on teste l'intégration
    data_dir = "backend/data/raw"
    return SearchEngine(data_dir=data_dir)

def test_search_by_brand_name(engine):
    """Vérifie qu'on trouve le Doliprane par son nom de marque."""
    results = engine.search("DOLIPRANE")
    assert len(results) > 0
    assert all("DOLIPRANE" in r.nom.upper() for r in results)

def test_search_by_substance_name(engine):
    """Vérifie qu'on trouve le Doliprane en tapant sa molécule (Paracétamol)."""
    results = engine.search("PARACÉTAMOL")
    assert len(results) > 0
    # On vérifie qu'au moins un des résultats est un Doliprane (princeps)
    assert any("DOLIPRANE" in r.nom.upper() for r in results)

def test_search_no_results(engine):
    """Vérifie qu'une recherche inconnue renvoie une liste vide."""
    results = engine.search("MOLÉCULE_INCONNUE_X")
    assert len(results) == 0
