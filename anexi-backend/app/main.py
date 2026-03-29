from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.observability.setup import setup_fastapi_observability
from app.routes import auth, orders, boutiques, dashboard, trust, payments, admin, events, timeline, trust_engine
import app.models  # ensure models are registered before metadata creation
import app.modules.trust.models  # ensure trust models are registered before metadata creation
import app.modules.events.models  # ensure events models are registered before metadata creation

# Create FastAPI app
app = FastAPI(
    title="Anexi.ai API",
    description="Intelligence layer for e-commerce - Trust scoring, AI calls, and business automation",
    version="1.0.0"
)
setup_fastapi_observability(app, service_name="anexi-backend")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables at startup if they don't exist yet
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(boutiques.router)
app.include_router(dashboard.router)
app.include_router(trust.router)
app.include_router(payments.router)
app.include_router(admin.router)
app.include_router(events.router)
app.include_router(timeline.router)
app.include_router(trust_engine.router)


@app.get("/")
def root():
    """
    API Root endpoint
    """
    return {
        "message": "Bienvenue sur Anexi.ai API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy"}
