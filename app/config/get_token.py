from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from app.config.database import get_session
from app.models.entities import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    repo = UserRepository(session)
    service = AuthService(repo)
    email = service.decode_token(token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user