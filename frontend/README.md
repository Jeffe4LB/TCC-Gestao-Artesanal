# Frontend — Gestão Artesanal

React + TypeScript + Vite + Ant Design.

## Desenvolvimento

```bash
npm install
npm run dev
```

API Django em `http://localhost:8000` (variável `VITE_API_URL` no `.env` se necessário).

## Qualidade

```bash
npm run lint        # ESLint
npm run lint:fix    # correções automáticas
npm run format      # Prettier
npm run build       # typecheck + build
```

Utilitários compartilhados: `src/utils/data.ts` (datas locais), `src/utils/moeda.ts` (BRL).

## Testes E2E (Playwright)

Requisitos: backend e frontend rodando; usuário válido no banco.

```bash
npm install
npx playwright install chromium

# Terminal 1 — backend
cd ../backend && ./venv/bin/python manage.py runserver

# Terminal 2 — E2E
cd frontend
export E2E_USERNAME=seu_usuario
export E2E_PASSWORD=sua_senha
npm run test:e2e
```

Interface interativa: `npm run test:e2e:ui`.

Relatório HTML: `npx playwright show-report`.

O teste `e2e/login.spec.ts` roda sem credenciais. Os cenários em `diferencial-*.spec.ts` são ignorados até `E2E_USERNAME` e `E2E_PASSWORD` estarem definidos.
