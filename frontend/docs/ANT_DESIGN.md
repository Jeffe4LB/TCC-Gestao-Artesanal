# Uso do Ant Design no frontend (Gestão Artesanal)

Este documento descreve **onde** a biblioteca [Ant Design](https://ant.design/) (antd **v6**) foi integrada, **quais componentes** são usados em cada área e **como** a aplicação se organiza em torno dela.

---

## 1. Dependências

| Pacote | Função |
|--------|--------|
| `antd` | Componentes de UI (layout, formulário, tabela, feedback, etc.). |
| `@ant-design/icons` | Ícones usados principalmente no menu lateral (`AppLayout`). |
| `dayjs` | Datas no formato esperado pelo `DatePicker` do antd; conversão para strings `YYYY-MM-DD` enviadas à API. |

Instalação (já refletida no `package.json`):

```bash
npm install antd @ant-design/icons dayjs
```

---

## 2. Configuração global

### 2.1 `src/providers/AntdAppProvider.tsx`

- Envolve toda a árvore React **abaixo** de `React.StrictMode`, em `src/main.tsx`.
- Usa **`ConfigProvider`** do antd com:
  - **`locale={ptBR}`** — import de `antd/locale/pt_BR` (textos de paginação, calendário, etc. em português).
  - **`theme`** — `algorithm: theme.defaultAlgorithm` e `token.colorPrimary: #2563eb` (alinhado ao azul já usado no projeto), `borderRadius: 6`.

**Como alterar o tema:** ajuste o objeto `theme` em `AntdAppProvider.tsx` (tokens globais) ou use `ConfigProvider` aninhado em páginas específicas.

### 2.2 `src/main.tsx`

Ordem de providers:

1. `AntdAppProvider` (antd + locale)
2. `App` (rotas, auth, toasts)

O CSS global legado (`src/index.css`) continua sendo importado em `main.tsx`; ele ainda cobre telas como **login**, **home pública** e o **hero** da home autenticada, além de classes utilitárias (`.loading-screen`, `.auth-page`, `.home-welcome-*`).

### 2.3 O que **não** passou pelo antd

- **`ToastProvider` / `useToast`** (`src/hooks/useToast.tsx`): notificações temporárias continuam com o componente customizado (pilha de toasts em CSS). Apenas a página **Categorias** ainda chama `showToast` após criar/editar/excluir.
- **`ProtectedRoute` / `useAuth`**: lógica de sessão inalterada; só a **UI do login** foi migrada para antd.

---

## 3. Layout autenticado: `src/components/layout/AppLayout.tsx`

Substitui o antigo `div.app-shell` + sidebar em HTML/CSS por:

| Componente antd | Uso |
|-----------------|-----|
| `Layout` | Estrutura geral `Sider` + área principal. |
| `Layout.Sider` | Menu lateral escuro, largura 240px, `breakpoint="lg"`, `collapsible`. |
| `Menu` | `mode="inline"`, `theme="dark"`, itens com `Link` do React Router. |
| `Layout.Header` | Barra superior com nome do usuário e botão **Sair**. |
| `Layout.Content` | `margin: 24`; renderiza `<Outlet />` das rotas filhas. |
| `Badge` | Contadores nos itens **Alertas** (estoque) e **Alertas financeiros**. |
| `Button` | Logout com ícone `LogoutOutlined`. |

**Ícones** (`@ant-design/icons`): `HomeOutlined`, `DashboardOutlined`, `TagsOutlined`, `InboxOutlined`, `DollarOutlined`, `FileTextOutlined`, `LogoutOutlined`.

**Estado do menu:**

- `openKeys`: submenus abertos; ao navegar, `pathOpenKeys` garante que o grupo da rota atual fique aberto.
- `selectedKeys`: derivado de `location.pathname` (inclui casos especiais como `/app` → item Início).

---

## 4. Paginação: `src/components/PaginationBar.tsx`

- Implementação baseada em **`Pagination`** do antd.
- Props: `page`, `totalCount`, `pageSize` (padrão 20), `onPageChange`.
- `showSizeChanger={false}`; `showTotal` exibe o total de itens em português.

Todas as listagens paginadas do app usam este componente abaixo de uma **`Table`** com `pagination={false}`.

---

## 5. Páginas e componentes antd por rota

Padrão comum nas telas de CRUD e listas:

- **`Typography.Title`** (nível 3 ou 4) para o título da página.
- **`Space`** (`direction="vertical"`, `size="large"`) para empilhar blocos.
- **`Card`** para filtros e formulários.
- **`Table`** + colunas tipadas com `ColumnsType` de `antd/es/table`.
- **`Spin`** para estado de carregamento.
- **`Alert`** (`type="error"`) para erros de API.
- **`Button`**, **`Input`**, **`Select`**, **`Form`**, **`Checkbox`**, **`InputNumber`** conforme necessário.
- **`Popconfirm`** no lugar de `window.confirm` para exclusões (onde aplicável).

### 5.1 Autenticação e público

| Arquivo | Componentes antd |
|---------|------------------|
| `src/pages/LoginPage.tsx` | `Card`, `Form`, `Input`, `Input.Password`, `Button`, `Alert`, `Spin`, `Typography` |
| `src/pages/PublicHomePage.tsx` | `Card`, `Typography`, `Button` |

### 5.2 Início e dashboard

| Arquivo | Componentes antd |
|---------|------------------|
| `src/pages/HomePage.tsx` | `Card`, `Typography` (hero continua com CSS `.home-welcome`) |
| `src/pages/DashboardPage.tsx` | `Row`, `Col`, `Card`, `Statistic`, `Button`, `InputNumber`, `Alert`, `Spin`, `Typography`, `Space`; ícone `ReloadOutlined` |

### 5.3 Cadastros

| Arquivo | Destaques |
|---------|-----------|
| `CategoriesPage.tsx` | `Form` inline para busca; `Popconfirm` em excluir. |
| `CustomersPage.tsx` | `Select` para filtro ativo/inativo; formulário em `Card`. |
| `SuppliersPage.tsx` | Mesmo padrão de clientes. |
| `ProductsPage.tsx` | Vários `Select` (categoria, tipo, ativo); SKU desabilitado na edição. |

### 5.4 Estoque

| Arquivo | Destaques |
|---------|-----------|
| `StockBalancesPage.tsx` | Filtros + tabela de saldos. |
| `StockMovementsPage.tsx` | Dois `Card` (novo lançamento e filtros da listagem); `Select` de tipo de movimento. |
| `StockAlertsPage.tsx` | Busca + tabela; `rowKey="product_id"`. |
| `RecipesPage.tsx` | Linhas dinâmicas de insumos com `Button` `+ Linha` (`PlusOutlined`); `Popconfirm` ao excluir. |
| `ProductionRunsPage.tsx` | Formulário de ordem com linhas de consumo; link **Ver** com `Typography.Link`. |
| `ProductionRunDetailPage.tsx` | `Descriptions`, `Table` de linhas, `Button` link voltar, `Alert`/`Spin` para estados. |

### 5.5 Financeiro

| Arquivo | Destaques |
|---------|-----------|
| `AccountsReceivablePage.tsx` | **`DatePicker`** (`format="YYYY-MM-DD"`) para vencimentos e filtros; valores sincronizados com estado string via `dayjs` / `dateString` no `onChange`. |
| `AccountsPayablePage.tsx` | Mesmo padrão de datas; `Select` de fornecedor com busca. |
| `CashFlowPage.tsx` | `DatePicker` no período; `Statistic` nos totais. |
| `FinanceAlertsPage.tsx` | `InputNumber` para dias à frente; quatro `Table` (vencidos / a vencer × pagar / receber). |

### 5.6 Relatórios

| Arquivo | Destaques |
|---------|-----------|
| `ReportsHomePage.tsx` | `Row` / `Col` / `Card` com `hoverable`; cada card é um `Link`. |
| `ReportStockPositionPage.tsx` | Filtros, botões atualizar/exportar, `Table`. |
| `ReportStockMovementsPage.tsx` | `DatePicker` + filtros; até 500 linhas na prévia. |
| `ReportStockLowPage.tsx` | Busca + tabela. |
| `ReportFinanceOpenPage.tsx` | `Card` de resumo + duas tabelas. |
| `ReportFinanceCashFlowReportPage.tsx` | `DatePicker` + `Statistic` em cards. |
| `ReportFinanceAgingPage.tsx` | Componente interno `BucketTable` montando `Table` a partir das faixas de envelhecimento. |

---

## 6. Datas (`DatePicker` + API)

O backend continua recebendo **strings `YYYY-MM-DD`**, como antes.

- Nos formulários de contas a pagar/receber e nos relatórios com período, o valor do `DatePicker` é convertido no `onChange`:
  - segundo parâmetro `dateString` (ou verificação de tipo) preenche o estado string.
- `dayjs(data)` é usado apenas para alimentar a prop `value` do `DatePicker`.

Se o usuário limpar o campo, o código recua para valores padrão onde faz sentido (ex.: relatórios com `firstDayOfMonthLocal` / `todayLocal`).

---

## 7. Estilo e coexistência com `index.css`

- O **shell** antigo (`.app-shell`, `.sidebar`, `.topbar`, `.content`) deixou de ser usado pelo layout autenticado; o antd passa a definir estrutura e espaçamentos principais.
- Classes antigas permanecem no `index.css` para:
  - páginas fora do `AppLayout` (login, home pública);
  - overlay da `HomePage`;
  - toasts (`.toast-stack`);
  - utilitários diversos.

---

## 8. Build e performance

- O build de produção passa a incluir o bundle do antd (e ícones usados). O Vite pode avisar chunk &gt; 500 kB; mitigações futuras incluem **lazy loading** de rotas (`React.lazy` + `Suspense`) ou importação sob demanda de submódulos do antd (política do projeto).

---

## 9. Referência rápida de arquivos tocados

| Categoria | Arquivos |
|-----------|----------|
| Config | `src/main.tsx`, `src/providers/AntdAppProvider.tsx` |
| Layout / shared | `src/components/layout/AppLayout.tsx`, `src/components/PaginationBar.tsx` |
| Páginas | Todos os `src/pages/**/*.tsx` listados nas seções acima |

Para alterar comportamento global do antd, comece por **`AntdAppProvider`**. Para o menu e cabeçalho logado, edite **`AppLayout`**.
