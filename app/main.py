# app/main.py
from fastapi import FastAPI
from app.api.routers import contratado_router # <-- IMPORTAR

app = FastAPI(
    title="SIGESCON API",
    description="Sistema de Gestão de Contratos",
    version="1.0.0"
)

# REGISTRAR O NOVO ROUTER
app.include_router(contratado_router.router)

@app.get("/", tags=["Root"])
def read_root():
    """
    Endpoint raiz da API.
    """
    return {"message": "Bem-vindo à SIGESCON API!"}