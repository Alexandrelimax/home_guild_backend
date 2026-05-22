from sqlmodel import Session, select, text, SQLModel
from app.models.entities import User, Badge, Reward, Quest, UserBadgeLink
from app.config.database import engine
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from datetime import datetime

def seed_database():
    import sys
    print("🌱 Recriando o Banco de Dados...")
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        print("🌱 Iniciando o Seed do Banco de Dados...")

        # --- SETUP PARA SENHAS REAIS ---
        repo = UserRepository(session)
        auth_service = AuthService(repo)
        password_padrao = auth_service.get_password_hash("senha123")
        password_admin = auth_service.get_password_hash("admin123")

        # 1. CATÁLOGO DE BADGES (CONQUISTAS)
        badges_list = [
            Badge(
                id=1,
                title="Despertar Higiênico",
                description="Tomou banho e escovou os dentes.",
                icon="assets/badges/despertar_higienico_icon.png",
                card_image="assets/badges/despertar_higienico_card.png",
                rarity="comum"
            ),
            Badge(
                id=2,
                title="Rei da Cozinha",
                description="Limpou a cozinha sem deixar rastros.",
                icon="assets/badges/rei-cozinha-icon2.png",
                card_image="assets/badges/rei-cozinha-card2.png",
                rarity="raro"
            ),
            Badge(
                id=3,
                title="Matador de Faxina",
                description="Limpou a casa no modo Hardcore.",
                icon="assets/badges/matador_faxina_icon2.png",
                card_image="assets/badges/matador_faxina_card2.png",
                rarity="lendario"
            ),
        ]
        for b in badges_list:
            session.merge(b)

        # 2. CATÁLOGO DE RECOMPENSAS
        rewards = [
            Reward(id=1, title="Açaí Turbinado", description="Um açaí de 500ml com tudo dentro.", cost=300, min_level=1, type="bits", icon="ice_cream"),
            Reward(id=2, title="Doce Especial", description="Aquele doce que você gosta.", cost=200, min_level=1, type="bits", icon="cookie"),
            Reward(id=3, title="Escolhe lanche no Sábado", description="Até R$100.", cost=500, min_level=1, type="bits", icon="cookie"),
            Reward(id=4, title="Resgate Amador", description="Troque 5 níveis por uma recompensa comum.", cost=0, min_level=5, type="milestone", icon="restaurant"),
            Reward(id=5, title="Recompensa de Elite", description="Troque 10 níveis por uma recompensa épica.", cost=0, min_level=10, type="milestone", icon="keyboard"),
            Reward(id=6, title="O Ápice da Jornada", description="Troque 15 níveis por uma recompensa lendária.", cost=0, min_level=15, type="milestone", icon="star")
        ]
        for r in rewards:
            session.merge(r)

        # 3. USUÁRIOS (GMs e PLAYERS)
        # --- GAME MASTERS ---
        user_admin_alexandre = User(
            id=1,
            name="Alexandre",
            email="alexandre@test.com",
            hashed_password=password_admin,
            role="admin",
            avatar="https://img.icons8.com/nolan/1200/administrator-male.png",
            xp=0, level=1, bits=0
        )
        user_admin_kate = User(
            id=2,
            name="Kate",
            email="kate@test.com",
            hashed_password=password_admin,
            role="admin",
            avatar="https://img.icons8.com/nolan/1200/female-profile.png",
            xp=0, level=1, bits=0
        )

        # --- PLAYERS ---
        user_dev_kaique = User(
            id=3,
            name="Kaique",
            email="kaique@test.com",
            hashed_password=password_padrao,
            role="user",
            avatar="https://img.freepik.com/vetores-premium/retrato-de-um-menino-africano-com-oculos-sorrindo_684058-1494.jpg?semt=ais_hybrid&w=740&q=80",
            xp=950, level=14, bits=1000
        )
        user_partner_manu = User(
            id=4,
            name="Manu",
            email="manu@test.com",
            hashed_password=password_padrao,
            role="user",
            avatar="https://img.freepik.com/vetores-gratis/menina-jovem-com-trancas_1308-176684.jpg?semt=ais_hybrid&w=740&q=80",
            xp=200, level=5, bits=500
        )
        
        for u in [user_admin_alexandre, user_admin_kate, user_dev_kaique, user_partner_manu]:
            session.merge(u)
        
        session.flush()

        # 4. VINCULANDO OS BADGES (Apenas para os Jogadores)
        print("🏅 Vinculando badges aos jogadores...")
        for user_id in [user_dev_kaique.id, user_partner_manu.id]:
            for badge in badges_list:
                link = UserBadgeLink(user_id=user_id, badge_id=badge.id)
                session.merge(link)

        # 5. QUESTS (Tarefas)
        quests = [
            # Quests Kaique (ID 3)
            Quest(title="Escovar os dentes e banho", xp=400, bits=100, user_id=3, status="pending"),
            Quest(title="Dobrar roupas", description="Dobrar todas as roupas do cesto e guardar na gaveta.", xp=350, bits=80, user_id=3, status="analyzing"),
            Quest(title="Lavar a louça", xp=250, bits=50, user_id=3, status="approved"),
            Quest(title="Lavar o Banheiro", xp=500, bits=150, user_id=3, status="pending"),
            # Quests Manu (ID 4)
            Quest(title="Secar e Guardar utensílios", xp=300, bits=60, user_id=4, status="pending"),
            Quest(title="Tirar roupa do Varal", xp=200, bits=40, user_id=4, status="analyzing"),
            Quest(title="Estudo Focado (2h)", description="Terminar módulo 2 de Angular", xp=450, bits=120, user_id=4, status="pending"),
            Quest(title="Lavar o Banheiro (Suíte)", xp=500, bits=150, user_id=4, status="pending"),
        ]
        
        for q in quests:
            session.add(q)
        
        session.commit()
        
        if engine.dialect.name == "postgresql":
            print("🔄 Sincronizando sequências do PostgreSQL...")
            session.exec(text("SELECT setval(pg_get_serial_sequence('user', 'id'), coalesce(max(id), 0) + 1, false) FROM \"user\";"))
            session.exec(text("SELECT setval(pg_get_serial_sequence('badge', 'id'), coalesce(max(id), 0) + 1, false) FROM \"badge\";"))
            session.exec(text("SELECT setval(pg_get_serial_sequence('reward', 'id'), coalesce(max(id), 0) + 1, false) FROM \"reward\";"))
            session.exec(text("SELECT setval(pg_get_serial_sequence('quest', 'id'), coalesce(max(id), 0) + 1, false) FROM \"quest\";"))
            session.commit()
            
        print("✅ Banco de dados populado com sucesso!")
        print(f"👉 Admins (GMs): alexandre@test.com | kate@test.com")
        print(f"👉 Players: kaique@test.com | manu@test.com")

if __name__ == "__main__":
    seed_database()