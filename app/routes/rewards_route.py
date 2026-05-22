from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.config.database import get_session
from app.services.gamification_service import GamificationService
from app.models.schema import RewardDTO, RewardRedeemResponse
from app.models.entities import User
from app.config.get_token import get_current_user


router_rewards = APIRouter(prefix="/rewards", tags=["Rewards"])

@router_rewards.get("/shop", response_model=List[RewardDTO])
def get_shop(
    current_user: User = Depends(get_current_user), 
    session: Session = Depends(get_session)
):
    return GamificationService(session).get_shop_data(current_user.id)


@router_rewards.post("/{reward_id}/redeem", response_model=RewardRedeemResponse)
def redeem_reward(
    reward_id: int, 
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    service = GamificationService(session)
    result = service.redeem_reward(reward_id, current_user.id)

    if not result:
        raise HTTPException(status_code=400, detail="Erro ao resgatar recompensa")

    return result