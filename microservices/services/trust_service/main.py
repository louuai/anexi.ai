import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.observability import setup_fastapi_observability
from app.routes import trust


app = FastAPI(
    title="Anexi Trust Service",
    version="1.0.0",
    description="Trust Layer and risk scoring APIs",
)
setup_fastapi_observability(app, service_name=os.getenv("OTEL_SERVICE_NAME", "trust-service"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trust.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "trust-service"}
