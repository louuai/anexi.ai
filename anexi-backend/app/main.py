from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routes import auth, orders, boutiques, dashboard, trust, payments, admin
import app.models  # ensure models are registered before metadata creation

# Create FastAPI app
app = FastAPI(
    title="Anexi.ai API",
    description="Intelligence layer for e-commerce - Trust scoring, AI calls, and business automation",
    version="1.0.0"
)

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
