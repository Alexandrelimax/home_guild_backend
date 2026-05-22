import bcrypt # Importe o bcrypt puro
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError

from app.models.entities import User
from app.repositories.user_repository import UserRepository
from app.models.schema import UserCreate
from app.config.settings import settings

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self._SECRET_KEY = settings.JWT_SECRET
        self._ALGORITHM = settings.JWT_ALGORITHM
        self._TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def authenticate(self, email: str, password: str) -> Optional[dict]:
        user = self.user_repo.get_by_email(email)
        
        if not user or not self._verify_password(password, user.hashed_password):
            return None
            
        # Colocamos o ID no payload para facilitar a vida do backend e do frontend
        token = self._create_access_token(data={
            "sub": user.email,
            "user_id": user.id  # <--- Adicionado aqui
        })
        return {
            "access_token": token, 
            "token_type": "bearer"
        }

    def register_user(self, user_data: UserCreate) -> User:
        if self.user_repo.get_by_email(user_data.email):
            raise ValueError("Este e-mail já está cadastrado.")

        new_user = User(
            name=user_data.name,
            email=str(user_data.email),
            hashed_password=self.get_password_hash(user_data.password),
            avatar=user_data.avatar,
            xp=0,
            level=1,
            bits=0
        )
        return self.user_repo.save(new_user)

    def decode_token(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, self._SECRET_KEY, algorithms=[self._ALGORITHM])
            return payload.get("sub")
        except JWTError:
            return None

    # --- MÉTODOS REFEITOS SEM PASSLIB ---

    def get_password_hash(self, password: str) -> str:
        # Transforma a string em bytes, gera o salt e faz o hash
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8') # Salva como string no banco

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        # Transforma tudo em bytes para comparar
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    # ------------------------------------

    def _create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self._SECRET_KEY, algorithm=self._ALGORITHM)