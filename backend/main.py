import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.api.routes import research, reports, auth, history
from app.core.config import settings
from prometheus_fastapi_instrumentator import Instrumentator

limiter = Limiter(key_func=lambda r: r.client.host)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Autonomous Multi-Agent Research System",
    version="1.0.0",
    redirect_slashes=False
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(research.router, prefix="/api/v1/research", tags=["research"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(history.router, prefix="/api/v1/history", tags=["history"])

Instrumentator().instrument(app).expose(app)

from app.models.database import engine, Base

@app.on_event("startup")
async def startup():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"DB init skipped: {e}")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
