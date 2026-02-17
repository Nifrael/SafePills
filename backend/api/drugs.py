from fastapi import APIRouter, HTTPException, Query, Request
from typing import List
from backend.core.limiter import limiter

from backend.core.schemas import SearchResult
from backend.core.models import Drug
from backend.services.search import search_medication, get_drug_details

router = APIRouter(prefix="/api", tags=["drugs"])

@router.get("/search", response_model=List[SearchResult])
@limiter.limit("30/minute")

async def search(request: Request, q: str = Query(..., min_length=2)):
    return search_medication(q)

@router.get("/drugs/{cis}", response_model=Drug)
@limiter.limit("30/minute")

async def get_details(request: Request, cis: str):
    drug = get_drug_details(cis)
    if not drug:
        raise HTTPException(status_code=404, detail="Médicament non trouvé")
    return drug
