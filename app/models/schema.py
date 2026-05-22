from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime

base_config = ConfigDict(from_attributes=True)


# =========================================
# AUTHENTICATION SCHEMAS
# =========================================

class UserCreate(BaseModel):
    name: str
    email: EmailStr  # Mudamos para EmailStr para validação automática
    password: str
    avatar: str

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# =========================================
# DTOs (Data Transfer Objects)
# =========================================

class UserDTO(BaseModel):
    id: int
    name: str
    email: str
    avatar: str
    xp: int
    level: int
    bits: int
    role: str

    model_config = base_config
    
class BadgeDTO(BaseModel):
    id: int
    title: str
    description: str
    icon: str
    card_image: str
    rarity: str

    model_config = base_config

class LogDTO(BaseModel):
    id: int
    message: str
    type: str
    created_at: datetime

    model_config = base_config

class QuestDTO(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    xp: int
    bits: int
    user_id: int
    status: str
    is_recurring: bool = False
    event_badge_id: Optional[int] = None
    updated_at: Optional[datetime] = None

    model_config = base_config

class EventQuestDTO(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    xp: int
    bits: int
    status: str
    badge: BadgeDTO
    updated_at: Optional[datetime] = None

    model_config = base_config

class QuestWithUserDTO(BaseModel):
    quest: QuestDTO
    user: UserDTO

    model_config = base_config

class QuestCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    xp: int
    bits: int
    is_recurring: bool = False
    target_user_ids: List[int]

class EventCreateRequest(BaseModel):
    title: str
    description: str
    xp: int
    bits: int
    badge_title: str
    badge_description: str
    badge_rarity: str
    badge_icon: str
    badge_card_image: str
    target_user_ids: List[int]

class UserMetricsDTO(BaseModel):
    user: UserDTO
    total_completed: int
    active_quests: int

class AdminAnalyticsResponse(BaseModel):
    users_metrics: List[UserMetricsDTO]
    system_metrics: dict

    model_config = base_config

class RewardDTO(BaseModel):
    id: int
    title: str
    description: str
    cost: int
    min_level: int
    type: str
    icon: str
    redeemed: bool = False

    model_config = base_config

# =========================================
# RESPONSE: DASHBOARD
# =========================================

class DashboardResponse(BaseModel):
    profile: UserDTO
    badges: List[BadgeDTO]
    recent_logs: List[LogDTO]
    active_quests: List[QuestDTO]

    model_config = base_config


# =========================================
# RESPONSE BASE
# =========================================

class BaseActionResponse(BaseModel):
    message: str
    new_logs: List[LogDTO] = []

    model_config = base_config


class QuestSubmitResponse(BaseActionResponse):
    quest: QuestDTO


class QuestReviewResponse(BaseActionResponse):
    user: UserDTO
    quest: QuestDTO
    leveled_up: bool


class RewardRedeemResponse(BaseActionResponse):
    user: Optional[UserDTO] = None
    reward: Optional[RewardDTO] = None