from fastapi import FastAPI, Query, HTTPException, Request
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os

from ..services.search_service import search_medication, get_drug_details
from ..core.schemas import SearchResult
from ..core.models import Drug
from .automedication import router as automedication_router
from .flow_endpoint import router as flow_router

# --- Rate Limiter (le "vigile" de l'API) ---
# get_remote_address = fonction qui récupère l'adresse IP du visiteur
# default_limits = limite par défaut pour TOUS les endpoints (filet de sécurité)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# En production, on cache la documentation (le plan de l'API).
# En dev, on la garde pour pouvoir tester facilement.
IS_PRODUCTION = os.getenv("ENV") == "production"

app = FastAPI(
    title="SafePills API",
    description="API KISS pour l'automédication sécurisée",
    version="1.0.0",
    docs_url=None if IS_PRODUCTION else "/docs",        # Page Swagger
    redoc_url=None if IS_PRODUCTION else "/redoc",       # Page ReDoc  
    openapi_url=None if IS_PRODUCTION else "/openapi.json"  # Schéma brut
)

# On attache le vigile à l'application
app.state.limiter = limiter
# Quand quelqu'un dépasse la limite → erreur 429 "Too Many Requests"
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuration CORS — restreint aux origines autorisées
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:4321,http://127.0.0.1:4321").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# --- Middleware "panneaux de sécurité" ---
# À chaque réponse, on colle des consignes de sécurité pour le navigateur.
# C'est comme mettre des panneaux à la sortie de la pharmacie.
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # 1. On laisse la requête passer normalement et on récupère la réponse
    response = await call_next(request)
    # 2. On ajoute nos "panneaux" à la réponse avant de l'envoyer au navigateur
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# 1. Endpoint Recherche (Rapide)
# Limite : 30 recherches par minute par personne (c'est de l'autocomplétion, ça peut aller vite)
@app.get("/api/search", response_model=List[SearchResult])
@limiter.limit("30/minute")
async def search(request: Request, q: str = Query(..., min_length=2)):
    """
    Autocomplétion : cherche médicaments et substances par nom.
    """
    return search_medication(q)

# 2. Endpoint Détails (Complet)
# Limite : 30 fiches par minute par personne (largement suffisant pour un usage normal)
@app.get("/api/drugs/{cis}", response_model=Drug)
@limiter.limit("30/minute")
async def get_details(request: Request, cis: str):
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
