FROM python:3.12-slim

# Instala o uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copia os arquivos de dependência primeiro (Cache de Camada)
COPY pyproject.toml uv.lock ./

# Instala as dependências
RUN uv sync --frozen

# Copia o resto do código
COPY . .

# Expõe a porta do FastAPI
EXPOSE 8000