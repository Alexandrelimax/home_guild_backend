from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List, Literal

from app.config.database import get_session
from app.config.get_token import get_current_user
from app.models.entities import User
from app.models.schema import (
    AdminAnalyticsResponse,
    QuestWithUserDTO,
    QuestCreateRequest,
    EventCreateRequest,
    UserDTO,
    QuestReviewResponse,
)
from app.services.admin_service import AdminService
from app.services.gamification_service import GamificationService

router_admin = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    return current_user


@router_admin.get("/analytics", response_model=AdminAnalyticsResponse)
def get_analytics(
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    return AdminService(session).get_analytics()


@router_admin.get("/users/players", response_model=List[UserDTO])
def get_players(
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    from app.repositories.user_repository import UserRepository
    return UserRepository(session).get_all_players()


@router_admin.post("/quests")
def create_quest(
    data: QuestCreateRequest,
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    count = AdminService(session).create_quests(data)
    return {"message": f"{count} quests criadas com sucesso."}


@router_admin.post("/quests/reset-daily")
def reset_daily_quests(
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    count = AdminService(session).reset_daily_quests()
    return {"message": f"{count} atividades recorrentes foram geradas para hoje!"}


@router_admin.post("/events")
def create_event(
    data: EventCreateRequest,
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    count = AdminService(session).create_event(data)
    return {"message": f"Evento criado e associado para {count} jogadores!"}


@router_admin.get("/quests/analyzing", response_model=List[QuestWithUserDTO])
def get_analyzing_quests(
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    return AdminService(session).get_analyzing_quests()


@router_admin.post("/quests/{quest_id}/status", response_model=QuestReviewResponse)
def review_quest(
    quest_id: int,
    status: Literal["approved", "rejected"],
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    result = GamificationService(session).review_quest(quest_id, status, current_admin.id)
    if not result:
        raise HTTPException(status_code=400, detail="Operação inválida ou permissão negada")
    return result
