# Gestão Artesanal

## PostgreSQL

Crie o banco e ajuste `DB_*` no `.env` (copie de `.env.example`):

```sql
CREATE DATABASE gestao_artesanal;
```

O projeto usa **apenas PostgreSQL**. Crie a base (`CREATE DATABASE gestao_artesanal;`) e preencha `DB_*` no `backend/.env` (copie de `.env.example`).

## Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edite .env: SECRET_KEY e DB_* (PostgreSQL)
python3 manage.py migrate
python3 manage.py createsuperuser
python3 manage.py runserver
```

No macOS, se `python` não existir, use **`python3`** (como acima). Com a venv ativada, `./venv/bin/python manage.py …` também funciona.

Sempre que **mudar de base** (novo Postgres, nova `DB_NAME`, etc.) ou aparecer no `runserver` aviso de *unapplied migrations*, corra de novo: `python3 manage.py migrate`. Sem isso, faltam tabelas (`notifications_usernotification`, `core_passwordresettoken`, …) e surgem erros 500.

- **Primeiro login (SPA e JWT):** o utilizador e a palavra-passe são os que definiu em `createsuperuser` (campo **nome de utilizador**, não confundir com o e-mail). O exemplo abaixo com `"password":"sua_senha"` é só ilustrativo — não é uma senha pré-definida do projeto.
- **Esqueci a senha:** a API responde sempre com a mesma mensagem genérica (por segurança). O e-mail só é enviado se existir utilizador com esse e-mail **e** se o SMTP estiver configurado (`EMAIL_HOST_PASSWORD` preenchido). Em desenvolvimento pode usar `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` e copiar o link do terminal do Django.
- **Depois de redefinir a senha** (`/redefinir-senha` com sucesso), a palavra-passe **antiga deixa de funcionar** — use só a nova. Se pediu recuperação com um e-mail partilhado por várias contas, o sistema pode enviar vários e-mails (uma conta por link); abra o link correspondente ao utilizador certo.
- **Registo (`POST /auth/register/`)** grava em `auth_user` no PostgreSQL configurado em `DB_*`. Para listar na mesma BD do servidor: `python3 manage.py list_auth_users` (mostra `ENGINE` e `NAME`). Para ver quem usa um e-mail: `python3 manage.py list_auth_users --email "seu@email.com"`. Utilizadores registados pela SPA **não são superuser** por omissão (não substituem o `createsuperuser` para aceder ao `/admin/` do Django).
- **Front:** use `npm run dev` (porta 5173) com o Django em `127.0.0.1:8000` para o proxy `/api` funcionar. Se usar `npm run build` + `vite preview`, o proxy também está configurado (porta 4173). Sem proxy, o registo não chega ao backend e nada é gravado. Em cada `201` no registo, o `runserver` regista `auth_register ok user_id=...`.
- Admin: http://127.0.0.1:8000/admin/
- Health (público): `GET` http://127.0.0.1:8000/api/v1/health/

### Fase 1 — API v1 + JWT

Rotas principais:

| Método | Caminho | Auth |
|--------|---------|------|
| GET | `/api/v1/health/` | Não |
| POST | `/api/v1/auth/register/` | Não — body: `username`, `password`, `email` (opcional) |
| POST | `/api/v1/auth/token/` | Não — body: `username`, `password` → retorna `access`, `refresh` |
| POST | `/api/v1/auth/token/refresh/` | Não — body: `refresh` |
| POST | `/api/v1/auth/token/verify/` | Não — body: `token` |
| GET | `/api/v1/auth/me/` | Sim — header `Authorization: Bearer <access>` |

Exemplo (após registrar usuário):

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sua_senha"}'
```

Endpoints ficam sob `/api/v1/...`. Paginação: `?page=1` (20 itens por página nas listagens).

### Fase 2 — Cadastros (JWT obrigatório)

| Recurso | Caminho base | Observação |
|--------|----------------|------------|
| Categorias | `/api/v1/categories/` | CRUD — `?search=`, `?ordering=name` |
| Fornecedores | `/api/v1/suppliers/` | CRUD — `?is_active=true\|false`, `?search=` |
| Produtos | `/api/v1/products/` | CRUD — `product_type`: `purchased` ou `manufactured`; `?category=<id>`, `?supplier=<id>`, `?is_active=`, `?search=`, `?ordering=` |
| Clientes | `/api/v1/customers/` | CRUD — `?is_active=`, `?search=` |

Campos principais do **produto**: `sku` (único), `name`, `description`, `category` (id), `supplier` (id, opcional), `product_type`, `unit`, `min_stock`, `is_active`. Na leitura vêm também `category_name` e `supplier_name`.

### Fase 3 — Estoque (JWT obrigatório)

| Recurso | Caminho | Uso |
|---------|---------|-----|
| Saldos | `GET /api/v1/stock-balances/` | `?product=<id>`, `?search=` |
| Movimentos | `GET/POST /api/v1/stock-movements/` | Listagem/auditoria; **POST** = entrada manual |
| Receita (BOM) | `/api/v1/recipes/` | CRUD — `product` = produto **manufactured** (um receita por produto); `lines`: `component`, `quantity_per_unit` |
| Produção | `GET/POST /api/v1/production-runs/` | **POST** baixa insumos + entra acabado na mesma transação |

**POST movimento manual** (`stock-movements`):

- `movement_type`: `purchase_in` (compra) — `quantity` > 0  
- `movement_type`: `adjustment` — `quantity` positivo ou negativo (ajuste de saldo)

**POST produção** (`production-runs`):

```json
{
  "product": <id do produto manufactured>,
  "quantity_produced": "2",
  "lines": [
    { "component": <id insumo>, "quantity_consumed": "10" }
  ],
  "notes": ""
}
```

As quantidades consumidas são informadas manualmente (podem seguir ou não a receita cadastrada). Novos produtos ganham saldo `0` automaticamente (signal + migração para dados antigos).

### Fase 4 — Alertas de estoque (MVP)

| Método | Caminho | Auth |
|--------|---------|------|
| GET | `/api/v1/stock-alerts/` | Sim (JWT) |

Retorna produtos **ativos** com `min_stock > 0` e **saldo atual ≤ estoque mínimo**. Campos: `product_id`, `sku`, `name`, `min_stock`, `current_quantity`, `gap` (quanto falta para o mínimo). Ordenação: maior `gap` primeiro (mais crítico). `?search=` filtra por SKU/nome.

Não há persistência de “alerta lido” nesta fase — sempre cálculo em tempo real.

### Fase 5 — Financeiro (JWT obrigatório)

| Recurso | Caminho | Uso |
|---------|---------|-----|
| Contas a pagar | `/api/v1/accounts-payable/` | CRUD — `status`: `open`, `paid`, `cancelled`; ao marcar `paid`, enviar `paid_at` (data efetiva do pagamento) |
| Contas a receber | `/api/v1/accounts-receivable/` | CRUD — `status`: `open`, `paid`, `cancelled`; ao marcar `paid`, enviar `received_at` |
| Fluxo de caixa | `GET /api/v1/cash-flow/?from=YYYY-MM-DD&to=YYYY-MM-DD` | Soma entradas (`received_at` no período) e saídas (`paid_at` no período), apenas lançamentos **pagos/recebidos** |
| Alertas financeiros | `GET /api/v1/finance-alerts/?days_ahead=7` | `overdue` (vencidas em aberto) e `due_soon` (vencem até hoje + N dias, em aberto) |

Filtros úteis nas listagens: `?status=`, `?supplier=` / `?customer=`, `?due_from=` e `?due_to=` (YYYY-MM-DD), `?search=`.

### Fase 6 — Relatórios (JWT obrigatório)

Todos aceitam `?export=csv` para baixar **CSV** (UTF-8 com BOM, separador `;`, compatível com Excel). Não use `?format=csv`: o Django REST Framework reserva `format` para negociação de conteúdo e responde 404 sem renderer `csv`.

| Relatório | GET | Parâmetros |
|-----------|-----|------------|
| Posição de estoque | `/api/v1/reports/stock/position/` | `?category=<id>`, `?search=` |
| Movimentações | `/api/v1/reports/stock/movements/` | **Obrigatório:** `?from=&to=` (YYYY-MM-DD); opcional: `?product=`, `?movement_type=`, `?limit=` (JSON, máx. 2000) |
| Abaixo do mínimo | `/api/v1/reports/stock/low/` | `?search=` |
| Em aberto | `/api/v1/reports/finance/open/` | — |
| Fluxo de caixa | `/api/v1/reports/finance/cash-flow/` | **Obrigatório:** `?from=&to=` (mesma regra do financeiro) |
| Envelhecimento | `/api/v1/reports/finance/aging/` | Faixas: vencidas; até 7 dias; 8–30 dias; após 30 dias (só **em aberto**) |

### Fase 7 — Notificações (MVP)

| Método | Caminho | Auth |
|--------|---------|------|
| GET | `/api/v1/notifications/summary/` | Sim (JWT) |

Consolida **estoque abaixo do mínimo** (contagem + prévia de itens) e **totais de alertas financeiros** (vencidas em aberto; quantidades a vencer até `today + days_ahead`). Query: `?days_ahead=7`, `?stock_preview=10` (máx. 50).

Os endpoints detalhados (`/api/v1/stock-alerts/`, `/api/v1/finance-alerts/`) continuam disponíveis.

**Frontend:** login com JWT (token em `localStorage`), botão “Carregar resumo de alertas” chamando o summary acima. Evolução futura: Celery + e-mail, WebSockets se precisar tempo real.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

- **Pública:** `/` — health check + link para login  
- **Login:** `/login`  
- **Área logada (JWT):** `/app` — dashboard de alertas  
- **Cadastros:** `/app/cadastros/categorias`, `/app/cadastros/fornecedores`, `/app/cadastros/clientes`, `/app/cadastros/produtos` — listagem, busca/filtros, paginação, criar/editar/excluir

Cliente HTTP: `src/api/client.ts` (GET/POST/PATCH/DELETE + **refresh** automático em 401). Sessão: `localStorage` (`access` / `refresh`). Rotas protegidas: `src/routes/ProtectedRoute.tsx` + `AuthProvider` em `src/hooks/useAuth.tsx`.

Abra http://127.0.0.1:5173 — proxy Vite para `/api` → backend `:8000`.

## CORS

Origens permitidas: `http://localhost:5173` e `http://127.0.0.1:5173` (ver `backend/config/settings.py`).
