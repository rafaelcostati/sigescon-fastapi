# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routers import contratado_router, auth_router, usuario_router, perfil_router, modalidade_router, status_router, status_relatorio_router, status_pendencia_router, contrato_router, pendencia_router
from app.core.database import get_db_pool, close_db_pool

# Gerenciador de contexto para o ciclo de vida da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando aplicação e criando pool de DB...")
    await get_db_pool()
    yield
    print("Fechando pool de DB...")
    await close_db_pool()
    
app = FastAPI(
    title="SIGESCON API",
    description="Sistema de Gestão de Contratos",
    version="1.0.0",
    lifespan=lifespan 
)

# Registrando os routers
app.include_router(contratado_router.router)
app.include_router(auth_router.router)
app.include_router(usuario_router.router)
app.include_router(perfil_router.router)
app.include_router(modalidade_router.router)
app.include_router(status_router.router)
app.include_router(status_relatorio_router.router)
app.include_router(status_pendencia_router.router)
app.include_router(contrato_router.router)
app.include_router(pendencia_router.router)

@app.get("/", tags=["Root"])
def read_root():
    """
    Endpoint raiz da API.
    """
    return {"message": "Bem-vindo à SIGESCON API!"}