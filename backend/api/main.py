from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging

from backend.core.config import settings
from backend.core.limiter import limiter
from backend.api.drugs import router as drugs_router
from backend.api.automedication import router as automedication_router
from backend.api.flow_endpoint import router as flow_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("safepills")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API pour l'automédication sécurisée",
    version=settings.VERSION,
    docs_url=None if settings.IS_PRODUCTION else "/docs",
    redoc_url=None if settings.IS_PRODUCTION else "/redoc",
    openapi_url=None if settings.IS_PRODUCTION else "/openapi.json"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
        
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

app.include_router(drugs_router)
app.include_router(automedication_router)
app.include_router(flow_router)

@app.get("/")
def read_root():
    return {
        "message": f"{settings.PROJECT_NAME} Ready", 
        "endpoints": [
            f"{settings.API_V1_STR}/search", 
            f"{settings.API_V1_STR}/drugs/{{cis}}", 
            f"{settings.API_V1_STR}/automedication/flow/{{cis}}"
        ]
    }
