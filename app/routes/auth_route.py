from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.config.database import get_session
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.models.entities import User
from app.models.schema import LoginRequest, Token, UserDTO, UserCreate
from app.config.get_token import get_current_user


router_auth = APIRouter(prefix="/auth", tags=["Authentication"])

@router_auth.post("/login", response_model=Token)
def login(login_data: LoginRequest, session: Session = Depends(get_session)):
    repo = UserRepository(session)
    service = AuthService(repo)
    result = service.authenticate(login_data.email, login_data.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="E-mail ou senha inválidos"
        )
    return result

@router_auth.post("/register", response_model=UserDTO, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    repo = UserRepository(session)
    service = AuthService(repo)
    try:
        return service.register_user(user_data)
    except ValueError as e:
        # Erro de e-mail já cadastrado cai aqui
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router_auth.get("/me", response_model=UserDTO)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Retorna o perfil do usuário logado. 
    Usado pelo Angular para validar a sessão no carregamento.
    """
    return current_user