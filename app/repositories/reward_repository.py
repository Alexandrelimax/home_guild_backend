from sqlmodel import Session, select
from app.repositories.base_repository import BaseRepository
from app.models.entities import Reward, UserRewardLink

class RewardRepository(BaseRepository[Reward]):
    def __init__(self, session: Session):
        super().__init__(session, Reward)
        
    def get_user_reward_ids(self, user_id: int) -> list[int]:
        """Busca apenas os IDs para o check de 'redeemed'"""
        statement = select(UserRewardLink.reward_id).where(UserRewardLink.user_id == user_id)
        results = self.session.exec(statement).all()
        return list(results)

    def get_user_rewards(self, user_id: int):
        statement = select(Reward).join(UserRewardLink).where(UserRewardLink.user_id == user_id)
        return self.session.exec(statement).all()