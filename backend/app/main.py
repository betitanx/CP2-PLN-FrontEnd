from fastapi import FastAPI
from app.config import Config
from app.core.orchestrator import Orchestrator
from app.api.routes import router


def criar_app():
    app = FastAPI(title='Prosa — Oficina Roda Certa', version='1.0.0',
                  description='Serviço conversacional fictício. Use Authorize para informar X-API-Key. Memória, estado, agenda e métricas vivem no backend.')
    app.state.bot = Orchestrator(Config())
    app.include_router(router)
    return app
