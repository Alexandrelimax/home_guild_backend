from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

# --- TABELAS DE LIGAÇÃO (MANY-TO-MANY) ---

class UserBadgeLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    badge_id: int = Field(foreign_key="badge.id", primary_key=True) 
    earned_at: datetime = Field(default_factory=datetime.now)

class UserRewardLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    reward_id: int = Field(foreign_key="reward.id", primary_key=True)
    redeemed_at: datetime = Field(default_factory=datetime.now)

# --- ENTIDADES PRINCIPAIS ---

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    avatar: str
    xp: int = Field(default=0)
    level: int = Field(default=1)
    bits: int = Field(default=0)
    role: str = Field(default="user") # 'admin' ou 'user'
    # Relacionamentos
    quests: List["Quest"] = Relationship(back_populates="user")
    logs: List["Log"] = Relationship(back_populates="user")
    badges: List["Badge"] = Relationship(back_populates="users", link_model=UserBadgeLink)
    rewards: List["Reward"] = Relationship(back_populates="users", link_model=UserRewardLink)

class Quest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None # Adicionado para suportar o seed
    xp: int
    bits: int
    status: str = Field(default="pending") # pending, approved, rejected
    user_id: int = Field(foreign_key="user.id")
    is_recurring: bool = Field(default=False)
    event_badge_id: Optional[int] = Field(default=None, foreign_key="badge.id")
    
    user: Optional[User] = Relationship(back_populates="quests")
    badge: Optional["Badge"] = Relationship()
    updated_at: datetime = Field(default_factory=datetime.now)

class Badge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True) 
    title: str
    description: str
    icon: str
    card_image: str
    rarity: str # comum, raro, lendario
    
    users: List[User] = Relationship(back_populates="badges", link_model=UserBadgeLink)

class Reward(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    cost: int  # Custo em Bits
    min_level: int = Field(default=1) 
    type: str = Field(default="bits")  # 'bits' ou 'milestone'
    icon: str
    
    users: List[User] = Relationship(back_populates="rewards", link_model=UserRewardLink)

class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    message: str
    type: str # info, error, levelup, approved, warning
    user_id: int = Field(foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="logs")
    created_at: datetime = Field(default_factory=datetime.now)