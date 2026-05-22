from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from app.config.database import get_session
from app.models.entities import User
from app.services.gamification_service import GamificationService
from app.models.schema import DashboardResponse, LogDTO, EventQuestDTO, BadgeDTO
from app.config.get_token import get_current_user
from app.repositories.log_repository import LogRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.badge_repository import BadgeRepository

router_users = APIRouter(prefix="/users", tags=["Users"])


@router_users.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    data = GamificationService(session).get_user_dashboard(current_user.id)
    if not data:
        raise HTTPException(status_code=404, detail="Dados do dashboard não encontrados")
    return data


@router_users.get("/notifications", response_model=List[LogDTO])
def get_notifications(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return LogRepository(session).get_notifications_by_user(current_user.id)


@router_users.get("/events", response_model=List[EventQuestDTO])
def get_event_quests(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    quests = QuestRepository(session).get_event_quests_by_user(current_user.id)
    badge_repo = BadgeRepository(session)
    result = []
    for q in quests:
        badge = badge_repo.get_by_id(q.event_badge_id)
        if badge:
            result.append(EventQuestDTO(
                id=q.id,
                title=q.title,
                description=q.description,
                xp=q.xp,
                bits=q.bits,
                status=q.status,
                badge=BadgeDTO.model_validate(badge),
                updated_at=q.updated_at,
            ))
    return result
