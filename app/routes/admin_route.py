from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from app.config.database import get_session
from app.config.get_token import get_current_user
from app.models.entities import User, Quest
from app.models.schema import (
    AdminAnalyticsResponse, UserMetricsDTO, QuestWithUserDTO, 
    QuestCreateRequest, EventCreateRequest, UserDTO, QuestDTO, QuestReviewResponse
)
from app.repositories.user_repository import UserRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.badge_repository import BadgeRepository
from app.services.gamification_service import GamificationService
from sqlmodel import select

router_admin = APIRouter(prefix="/admin", tags=["Admin"])

def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    return current_user

@router_admin.get("/analytics", response_model=AdminAnalyticsResponse)
def get_analytics(
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    user_repo = UserRepository(session)
    quest_repo = QuestRepository(session)
    
    players = user_repo.get_all_players()
    users_metrics = []
    
    for player in players:
        completed = quest_repo.get_user_quests(player.id, status="approved")
        active = quest_repo.get_user_quests(player.id, status="pending")
        users_metrics.append(UserMetricsDTO(
            user=UserDTO.model_validate(player),
            total_completed=len(completed),
            active_quests=len(active)
        ))
        
    system_metrics = {
        "pending_analysis": quest_repo.get_quests_count_by_status("analyzing"),
        "total_approved": quest_repo.get_quests_count_by_status("approved"),
        "total_rejected": quest_repo.get_quests_count_by_status("rejected"),
        "total_players": len(players)
    }

    return AdminAnalyticsResponse(
        users_metrics=users_metrics,
        system_metrics=system_metrics
    )

@router_admin.get("/users/players", response_model=List[UserDTO])
def get_players(
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    user_repo = UserRepository(session)
    return user_repo.get_all_players()

@router_admin.post("/quests")
def create_quest(
    data: QuestCreateRequest,
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    quest_repo = QuestRepository(session)
    user_repo = UserRepository(session)
    
    created_quests = []
    for uid in data.target_user_ids:
        player = user_repo.get_by_id(uid)
        if player:
            new_quest = Quest(
                title=data.title,
                description=data.description,
                xp=data.xp,
                bits=data.bits,
                user_id=player.id,
                status="pending",
                is_recurring=data.is_recurring
            )
            quest_repo.save(new_quest)
            created_quests.append(new_quest)
            
    return {"message": f"{len(created_quests)} quests criadas com sucesso."}

@router_admin.post("/quests/reset-daily")
def reset_daily_quests(
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    # Encontra templates de tarefas que são recorrentes
    templates = session.exec(
        select(Quest.title, Quest.description, Quest.xp, Quest.bits, Quest.user_id)
        .where(Quest.is_recurring == True)
        .distinct()
    ).all()
    
    quest_repo = QuestRepository(session)
    count = 0
    for title, desc, xp, bits, uid in templates:
        # Evita duplicar se ja existir pending para essa pessoa com mesmo titulo
        existing = session.exec(
            select(Quest).where(
                Quest.user_id == uid, 
                Quest.title == title,
                Quest.status == "pending"
            )
        ).first()
        
        if not existing:
            new_quest = Quest(
                title=title,
                description=desc,
                xp=xp,
                bits=bits,
                user_id=uid,
                status="pending",
                is_recurring=True # As cópias continuam mantendo a flag, o SQL distinct agrupa
            )
            quest_repo.save(new_quest)
            count += 1
            
    return {"message": f"{count} atividades recorrentes foram geradas para hoje!"}

@router_admin.post("/events")
def create_event(
    data: EventCreateRequest,
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    from app.models.entities import Badge
    badge_repo = BadgeRepository(session)
    quest_repo = QuestRepository(session)
    user_repo = UserRepository(session)
    
    # 1. Cria a Conquista (Badge) do Evento
    event_badge = Badge(
        title=data.badge_title,
        description=data.badge_description,
        icon=data.badge_icon,
        card_image=data.badge_card_image,
        rarity=data.badge_rarity
    )
    badge_repo.save(event_badge)
    
    # 2. Distribui a Quest com o badge associado
    created_quests = []
    for uid in data.target_user_ids:
        player = user_repo.get_by_id(uid)
        if player:
            new_quest = Quest(
                title=data.title,
                description=data.description,
                xp=data.xp,
                bits=data.bits,
                user_id=player.id,
                status="pending",
                event_badge_id=event_badge.id
            )
            quest_repo.save(new_quest)
            created_quests.append(new_quest)
            
    return {"message": f"Evento criado e associado para {len(created_quests)} jogadores!"}

@router_admin.get("/quests/analyzing", response_model=List[QuestWithUserDTO])
def get_analyzing_quests(
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    quest_repo = QuestRepository(session)
    user_repo = UserRepository(session)
    
    quests = quest_repo.get_analyzing_quests()
    result = []
    for q in quests:
        player = user_repo.get_by_id(q.user_id)
        if player:
            result.append(QuestWithUserDTO(
                quest=QuestDTO.model_validate(q),
                user=UserDTO.model_validate(player)
            ))
            
    return result

@router_admin.post("/quests/{quest_id}/status", response_model=QuestReviewResponse)
def review_quest(
    quest_id: int, 
    status: str, 
    current_admin: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    service = GamificationService(session)
    
    # Adicionamos current_admin.id para logs de aprovação (se necessário no futuro)
    result = service.review_quest(quest_id, status, current_admin.id)
    
    if not result:
        raise HTTPException(status_code=400, detail="Operação inválida ou permissão negada")
    
    return result
