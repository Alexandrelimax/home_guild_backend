from sqlmodel import Session
from app.models.schema import RewardDTO
from app.repositories.user_repository import UserRepository
from app.repositories.quest_repository import QuestRepository
from app.repositories.log_repository import LogRepository
from app.repositories.reward_repository import RewardRepository
from app.repositories.badge_repository import BadgeRepository
from typing import List

class GamificationService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.quest_repo = QuestRepository(session)
        self.log_repo = LogRepository(session)
        self.reward_repo = RewardRepository(session)
        self.badge_repo = BadgeRepository(session)

    # =========================================
    # QUESTS
    # =========================================

    def submit_quest(self, quest_id: int, user_id: int):
        quest = self.quest_repo.get_by_id(quest_id)
        
        # Garante que a quest existe, pertence ao usuário logado e está pendente
        if not quest or quest.user_id != user_id or quest.status != "pending":
            return None

        quest.status = "analyzing"
        self.quest_repo.save(quest)

        log = self.log_repo.create_log(
            user_id=quest.user_id,
            message=f"Quest '{quest.title}' enviada para análise.",
            log_type="analyzing"
        )

        return {
            "message": "Quest enviada para análise",
            "quest": quest,
            "new_logs": [log]
        }

    def review_quest(self, quest_id: int, new_status: str, reviewer_id: int):
        quest = self.quest_repo.get_by_id(quest_id)
        if not quest or quest.status != "analyzing":
            return None

        user = self.user_repo.get_by_id(quest.user_id)
        old_level = user.level
        logs = []

        if new_status == "approved":
            user.bits += quest.bits
            quest.status = "approved"

            if user.level < 15:
                user.xp += quest.xp
                while user.xp >= 1000:
                    user.level += 1
                    if user.level >= 15:
                        user.level, user.xp = 15, 0
                        logs.append(self.log_repo.create_log(user.id, "Você alcançou o nível máximo! 🏆", "legendary_unlock"))
                        break
                    else:
                        user.xp -= 1000
                        logs.append(self.log_repo.create_log(user.id, f"Nível {user.level} alcançado! 🚀", "levelup"))
            
            # --- PREMIAÇÃO DE BADGE POR EVENTO ---
            if quest.event_badge_id:
                badge = self.badge_repo.get_by_id(quest.event_badge_id)
                if badge and badge not in user.badges:
                    user.badges.append(badge)
                    logs.append(self.log_repo.create_log(user.id, f"🏆 Conquista Desbloqueada: {badge.title}!", "badge_unlocked"))

            msg, log_type = f"Quest '{quest.title}' aprovada!", "approved"

        elif new_status == "rejected":
            penalidade = quest.xp // 2
            user.xp -= penalidade
            
            # Lógica de downgrade de nível se o XP ficar negativo
            while user.xp < 0 and user.level > 1:
                user.level -= 1
                user.xp = 1000 + user.xp
                logs.append(self.log_repo.create_log(user.id, f"ALERTA: Downgrade para Nível {user.level}.", "downgrade"))
            
            if user.level == 1 and user.xp < 0: 
                user.xp = 0
                
            quest.status = "pending"
            msg, log_type = f"Quest '{quest.title}' rejeitada.", "rejected"

        # Persistência
        logs.append(self.log_repo.create_log(user.id, msg, log_type))
        self.user_repo.save(user)
        self.quest_repo.save(quest)

        return {
            "message": f"Quest {new_status} com sucesso",
            "leveled_up": user.level > old_level,
            "user": user,
            "quest": quest,
            "new_logs": logs
        }

    # =========================================
    # REWARDS
    # =========================================

    def redeem_reward(self, reward_id: int, user_id: int):
        user = self.user_repo.get_by_id(user_id)
        reward = self.reward_repo.get_by_id(reward_id)

        if not user or not reward: 
            return None

        if reward.type == "milestone":
            if user.level < reward.min_level: 
                return None
            
            user.level -= reward.min_level
            # Garante que não desça abaixo do nível 1
            if user.level < 1: 
                user.level, user.xp = 1, 0
                
            msg = f"LOJA: Você usou {reward.min_level} níveis por '{reward.title}'."
        else:
            if user.bits < reward.cost: 
                return None
            
            user.bits -= reward.cost
            msg = f"LOJA: Compra de '{reward.title}' por {reward.cost} Bits."

        # Adição na tabela de link e persistência
        user.rewards.append(reward)
        log = self.log_repo.create_log(user.id, msg, "info")
        
        self.user_repo.save(user)

        return {
            "message": "Resgate concluído", 
            "user": user, 
            "reward": reward, 
            "new_logs": [log]
        }

    # =========================================
    # DASHBOARD & SHOP
    # =========================================

    def get_user_dashboard(self, user_id: int):
        user = self.user_repo.get_by_id(user_id)
        if not user: 
            return None

        return {
            "profile": user,
            "badges": user.badges,
            "recent_logs": self.log_repo.get_latest_by_user(user_id, limit=15),
            "active_quests": self.quest_repo.get_user_quests(user_id)
        }

    def get_shop_data(self, user_id: int):
        all_rewards = self.reward_repo.list_all()
        user_reward_ids = self.reward_repo.get_user_reward_ids(user_id) 

        shop_items = []
        for r in all_rewards:
            reward_data = RewardDTO.model_validate(r)
            reward_data.redeemed = r.id in user_reward_ids 
            shop_items.append(reward_data)

        return shop_items