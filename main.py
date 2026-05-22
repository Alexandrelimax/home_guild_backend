from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.routes.dashboard_route import router_users
from app.routes.quests_route import router_quests
from app.routes.rewards_route import router_rewards
from app.routes.logs_route import router_logs
from app.routes.auth_route import router_auth
from app.routes.admin_route import router_admin

from app.config.database import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas no Postgres se não existirem
    init_db()
    yield

app = FastAPI(title="Gamification API", lifespan=lifespan)

# Configuração de CORS para o seu Angular (Porta 4200)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro das Rotas
app.include_router(router_users)
app.include_router(router_quests)
app.include_router(router_rewards)
app.include_router(router_logs)
app.include_router(router_auth)
app.include_router(router_admin)


@app.get("/")
def health_check():
    return {"status": "online", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)