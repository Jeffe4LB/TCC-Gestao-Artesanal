# Gestão Artesanal — TCC

Sistema web para gestão de pequenos negócios artesanais: cadastros, estoque, produção com receita (BOM), financeiro, relatórios e notificações.

## Stack

| Camada | Tecnologias |
|--------|-------------|
| Backend | Python, Django, Django REST Framework, JWT |
| Frontend | React, TypeScript, Vite, Ant Design |
| Banco | SQLite (dev) / PostgreSQL (produção) |

## Estrutura

```
projeto_gest_art/
├── backend/     # API REST
└── frontend/    # Interface web
```

## Desenvolvimento local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # edite SECRET_KEY e demais variáveis
python manage.py migrate
python manage.py runserver
```

API em `http://localhost:8000/api/v1/`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App em `http://localhost:5173`.

## Testes

```bash
# Backend
cd backend && ./venv/bin/python manage.py test

# Frontend E2E (backend + frontend rodando)
cd frontend
export E2E_USERNAME=seu_usuario
export E2E_PASSWORD=sua_senha
npm run test:e2e
```

## Produção

Use `DJANGO_SETTINGS_MODULE=config.settings_prod` e configure as variáveis descritas em `backend/.env.example`.

## Licença

Projeto acadêmico — TCC, UFTPR, Análise e Desenvolvimento de Sistemas.
