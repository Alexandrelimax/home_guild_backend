from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import List
from app.config.database import get_session
from app.services.gamification_service import GamificationService
from app.models.schema import LogDTO
from app.models.entities import User
from app.config.get_token import get_current_user

router_logs = APIRouter(prefix="/logs", tags=["Logs"])

@router_logs.get("", response_model=List[LogDTO]) # Tirei o /{user_id}
def get_history(
    limit: int = 50, 
    current_user: User = Depends(get_current_user), # <--- Use o Token
    session: Session = Depends(get_session)
):
    service = GamificationService(session)
    return service.log_repo.get_latest_by_user(current_user.id, limit=limit)