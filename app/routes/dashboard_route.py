from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.config.database import get_session
from app.models.entities import User
from app.services.gamification_service import GamificationService
from app.models.schema import DashboardResponse
from app.config.get_token import get_current_user

router_users = APIRouter(prefix="/users", tags=["Users"])

@router_users.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user), # <--- Extrai o usuário do Token
    session: Session = Depends(get_session)
):
    service = GamificationService(session)
    
    # Agora usamos o ID que veio do token validado
    data = service.get_user_dashboard(current_user.id)
    
    if not data:
        raise HTTPException(status_code=404, detail="Dados do dashboard não encontrados")
    
    return data