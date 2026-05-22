# Home Guild — Backend

> Sistema de gamificação de tarefas domésticas. Transforma afazeres cotidianos em quests de RPG, recompensando jogadores com XP, níveis, Bits e conquistas.

---

## Visão Geral

O sistema é dividido em dois papéis: **Admin** e **Player**.

- O **Admin** cria e distribui quests, cria eventos especiais, aprova ou rejeita as tarefas submetidas pelos jogadores e gerencia a loja de recompensas.
- O **Player** recebe quests, as envia para revisão quando concluídas, acumula XP e Bits, sobe de nível e resgata recompensas.

---

## Entidades de Negócio

### User
Representa tanto admins quanto players. O campo `role` diferencia os dois (`"admin"` ou `"user"`). Players acumulam `xp`, `level` e `bits`.

### Quest
Tarefa atribuída a um player específico. Passa por um ciclo de vida com quatro estados: `pending → analyzing → approved | pending (rejeitada)`.

### Badge
Conquista desbloqueada por eventos especiais. Associada a um player via tabela de ligação. Cada badge tem raridade: `comum`, `raro` ou `lendario`.

### Reward
Recompensa disponível na loja. Pode ser comprada com **Bits** (`type: "bits"`) ou desbloqueada gastando **níveis** acumulados (`type: "milestone"`).

### Log
Registro de toda ação relevante do sistema (aprovações, rejeições, level ups, compras). É a linha do tempo do player.

---

## Diagrama de Entidades

```mermaid
erDiagram
    User ||--o{ Quest : "recebe"
    User ||--o{ Log : "gera"
    User }o--o{ Badge : "conquista"
    User }o--o{ Reward : "resgata"
    Quest }o--o| Badge : "pode conceder"

    User {
        int id
        string name
        string email
        string role
        int xp
        int level
        int bits
    }

    Quest {
        int id
        string title
        string status
        int xp
        int bits
        bool is_recurring
        int event_badge_id
    }

    Badge {
        int id
        string title
        string rarity
    }

    Reward {
        int id
        string title
        string type
        int cost
        int min_level
    }

    Log {
        int id
        string message
        string type
        datetime created_at
    }
```

---

## Fluxos Principais

### 1. Autenticação

O frontend Angular autentica via email/senha e recebe um JWT com validade de 24h. Todas as rotas protegidas validam esse token.

```mermaid
sequenceDiagram
    participant Angular
    participant API
    participant DB

    Angular->>API: POST /auth/login {email, password}
    API->>DB: Busca user por email
    DB-->>API: User + hashed_password
    API->>API: bcrypt.checkpw()
    API-->>Angular: { access_token, token_type }

    Note over Angular: Armazena token e user_id

    Angular->>API: GET /auth/me (Bearer token)
    API->>API: Decodifica JWT → email
    API->>DB: Busca user por email
    API-->>Angular: UserDTO (perfil completo)
```

---

### 2. Ciclo de Vida de uma Quest

```mermaid
stateDiagram-v2
    direction LR

    [*] --> pending : Admin cria quest
    pending --> analyzing : Player envia para revisão
    analyzing --> approved : Admin aprova
    analyzing --> pending : Admin rejeita\n(volta para o player tentar novamente)
    approved --> [*]
```

**Quests recorrentes** (`is_recurring: true`) são templates que o admin pode replicar diariamente via `POST /admin/quests/reset-daily`. O sistema verifica se já existe uma cópia pendente para o mesmo player antes de criar uma nova.

---

### 3. Fluxo de Aprovação e Gamificação

Quando o admin aprova uma quest, o motor de gamificação calcula XP, nível e verifica se um badge de evento deve ser concedido.

```mermaid
flowchart TD
    A[Admin aprova quest] --> B[+Bits ao player]
    B --> C{Player está no nível máximo?\nnível 15}
    C -- Sim --> D[XP não é adicionado]
    C -- Não --> E[+XP ao player]
    E --> F{XP acumulado >= 1000?}
    F -- Não --> G[Mantém nível atual]
    F -- Sim --> H[Level Up!]
    H --> I[XP -= 1000]
    I --> J{Atingiu nível 15?}
    J -- Sim --> K[Nível máximo travado\nXP zerado]
    J -- Não --> F
    B --> L{Quest tem badge de evento?}
    L -- Sim --> M{Player já tem o badge?}
    M -- Não --> N[Badge concedido]
    M -- Sim --> O[Ignorado]
    L -- Não --> O
```

**Rejeição** penaliza o player com metade do XP da quest. Se o XP ficar negativo, o player faz downgrade de nível (cada nível perdido restaura 1000 XP).

```mermaid
flowchart TD
    A[Admin rejeita quest] --> B[Quest volta para pending]
    B --> C[XP -= metade do XP da quest]
    C --> D{XP ficou negativo e nível > 1?}
    D -- Sim --> E[Level Down]
    E --> F[XP += 1000]
    F --> D
    D -- Não --> G{Nível == 1 e XP ainda negativo?}
    G -- Sim --> H[XP travado em 0]
    G -- Não --> I[Fim]
```

---

### 4. Loja de Recompensas

Existem dois tipos de recompensa, com mecânicas distintas:

```mermaid
flowchart TD
    A[Player tenta resgatar reward] --> B{Tipo da reward}

    B -- bits --> C{Bits do player >= custo?}
    C -- Não --> D[❌ Recusado]
    C -- Sim --> E[Debita Bits do player]
    E --> F[✅ Reward registrada]

    B -- milestone --> G{Nível do player >= min_level?}
    G -- Não --> D
    G -- Sim --> H[Debita níveis do player\nplayer.level -= min_level]
    H --> I{Nível ficou abaixo de 1?}
    I -- Sim --> J[Trava em nível 1\nXP zerado]
    I -- Não --> F
```

| Tipo | Moeda | Detalhe |
|---|---|---|
| `bits` | Bits | Compra direta pelo saldo acumulado |
| `milestone` | Níveis | Gasta níveis conquistados — mecânica de prestígio |

---

### 5. Eventos Especiais

Admins podem criar eventos que distribuem uma quest com um badge exclusivo atrelado. Ao ter a quest aprovada, o player recebe o badge automaticamente.

```mermaid
flowchart LR
    A[Admin cria evento] --> B[Cria Badge\nexclusivo do evento]
    B --> C[Distribui Quest para\ncada player selecionado]
    C --> D[Quest com event_badge_id]
    D --> E{Quest aprovada}
    E -- Sim --> F[Badge concedido ao player\nse ainda não tiver]
    E -- Não --> G[Badge não concedido]
```

---

## Regras de Negócio

| Regra | Valor |
|---|---|
| XP por nível | 1000 |
| Nível máximo | 15 |
| Penalidade por rejeição | 50% do XP da quest |
| Nível mínimo | 1 (nunca desce abaixo) |
| Validade do token JWT | 24 horas |
| Logs por consulta (padrão) | 20 mais recentes |

---

## Rotas por Domínio

### Autenticação `/auth`
| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/register` | Cadastra novo player |
| POST | `/auth/login` | Retorna JWT |
| GET | `/auth/me` | Retorna perfil do usuário logado |

### Player `/users` `/quests` `/rewards` `/logs`
| Método | Rota | Descrição |
|---|---|---|
| GET | `/users/dashboard` | Perfil, badges, logs recentes e quests ativas |
| POST | `/quests/{id}/submit` | Envia quest para revisão |
| GET | `/rewards/shop` | Lista recompensas com flag `redeemed` |
| POST | `/rewards/{id}/redeem` | Resgata uma recompensa |
| GET | `/logs` | Histórico de ações do player |

### Admin `/admin`
| Método | Rota | Descrição |
|---|---|---|
| GET | `/admin/analytics` | Métricas de todos os players e do sistema |
| GET | `/admin/users/players` | Lista todos os players |
| GET | `/admin/quests/analyzing` | Quests aguardando revisão |
| POST | `/admin/quests/{id}/status` | Aprova ou rejeita uma quest |
| POST | `/admin/quests` | Cria quests para um ou mais players |
| POST | `/admin/quests/reset-daily` | Regenera quests recorrentes do dia |
| POST | `/admin/events` | Cria evento com badge exclusivo |
