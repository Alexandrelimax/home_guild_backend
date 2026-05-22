from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.config.database import get_session
from app.services.gamification_service import GamificationService
from app.models.schema import QuestSubmitResponse, QuestReviewResponse
from app.models.entities import User
from app.config.get_token import get_current_user


router_quests = APIRouter(prefix="/quests", tags=["Quests"])

@router_quests.post("/{quest_id}/submit", response_model=QuestSubmitResponse)
def submit_quest(
    quest_id: int, 
    current_user: User = Depends(get_current_user), 
    session: Session = Depends(get_session)
):
    service = GamificationService(session)
    result = service.submit_quest(quest_id, current_user.id)

    if result is None:
        raise HTTPException(
            status_code=400, 
            detail="Não foi possível submeter esta quest. Verifique se ela é sua ou se já foi enviada."
        )
    
    return result
    