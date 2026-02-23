import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.observability import setup_fastapi_observability
from app.routes import orders, boutiques


app = FastAPI(
    title="Anexi Orders Service",
    version="1.0.0",
    description="Orders and boutiques domain service",
)
setup_fastapi_observability(app, service_name=os.getenv("OTEL_SERVICE_NAME", "orders-service"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders.router)
app.include_router(boutiques.router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "orders-service"}
