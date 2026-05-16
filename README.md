# Patinhas Protegidas
# Configuração do projeto

## 1. Criar .venv

python -m venv .venv

## 2. Ativar ambiente

### Windows
.venv\Scripts\activate

### Mac/Linux
source .venv/bin/activate

## 3. Instalar dependências

pip install -r requirements.txt

## 4. Configurar .env

Adicionar credenciais do banco Aiven.

## 5. Rodar migration

python database/init_db.py

## 6. Rodar projeto

python app.py