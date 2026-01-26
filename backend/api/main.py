from fastapi import FastAPI, Query
from typing import List
from backend.services.search_service import search_drugs
from backend.core.models import Drug
import os

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SafePills API",
    description="API pour l'analyse des interactions médicamenteuses",
    version="0.1.0"
)

# Configuration CORS pour permettre au Frontend (port 4321) de parler au Backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En développement, on peut être permissif
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/search", response_model=List[Drug])
async def get_drug_search(q: str = Query(..., min_length=2)):
    """
    Reçoit une requête textuelle et renvoie la liste des médicaments 
    avec leurs substances depuis la base SQLite.
    """
    results = search_drugs(q)
    return results

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API SafePills"}
