import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.observability import setup_fastapi_observability
from app.routes import admin, auth


app = FastAPI(
    title="Anexi Auth Service",
    version="1.0.0",
    description="Authentication and account/profile service",
)
setup_fastapi_observability(app, service_name=os.getenv("OTEL_SERVICE_NAME", "auth-service"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "auth-service"}
