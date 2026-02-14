from fastapi import FastAPI, Query, HTTPException
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import os

from ..services.search_service import search_medication, get_drug_details
from ..core.schemas import SearchResult
from ..core.models import Drug
from .automedication import router as automedication_router
from .flow_endpoint import router as flow_router

app = FastAPI(
    title="SafePills API",
    description="API KISS pour l'automédication sécurisée",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Endpoint Recherche (Rapide)
@app.get("/api/search", response_model=List[SearchResult])
async def search(q: str = Query(..., min_length=2)):
    """
    Autocomplétion : cherche médicaments et substances par nom.
    """
    return search_medication(q)

# 2. Endpoint Détails (Complet)
@app.get("/api/drugs/{cis}", response_model=Drug)
async def get_details(cis: str):
    """
    Récupère la fiche complète d'un médicament (Substances + Tags).
    """
    drug = get_drug_details(cis)
    if not drug:
        raise HTTPException(status_code=404, detail="Médicament non trouvé")
    return drug

# 3. Router Automédication (Questions & Score)
app.include_router(automedication_router)

# 4. Router Flux unifié (Nouveau parcours)
app.include_router(flow_router)

@app.get("/")
def read_root():
    return {
        "message": "SafePills API Ready", 
        "endpoints": ["/api/search", "/api/drugs/{cis}", "/api/automedication/questions/{cis}"]
    }
