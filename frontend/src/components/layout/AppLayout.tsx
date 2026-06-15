import {
  DashboardOutlined,
  DollarOutlined,
  FileTextOutlined,
  HomeOutlined,
  InboxOutlined,
  LogoutOutlined,
  TagsOutlined,
  TeamOutlined,
} from "@ant-design/icons";
import { Badge, Button, Grid, Layout, Menu, theme, Tooltip, type MenuProps } from "antd";
import { useEffect, useMemo, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useAutenticacao } from "../../hooks/useAutenticacao";
import { ROTULOS_PAPEL } from "../../types/autenticacao";
import { useContagemFinanceiroVencido } from "../../hooks/useContagemFinanceiroVencido";
import { useContagemAlertaEstoque } from "../../hooks/useContagemAlertaEstoque";
import { CabecalhoNotificacoes } from "./CabecalhoNotificacoes";
import logo from "../../assets/logo.png";

const { Header, Sider, Content } = Layout;

type MenuItem = Required<MenuProps>["items"][number];

function item(
  key: string,
  label: React.ReactNode,
  icon?: React.ReactNode,
  children?: MenuItem[],
): MenuItem {
  return { key, icon, label, children } as MenuItem;
}

export function AppLayout() {
  const { user, logout } = useAutenticacao();
  const location = useLocation();
  const stockAlerts = useContagemAlertaEstoque();
  const financeOverdue = useContagemFinanceiroVencido();
  const { token } = theme.useToken();
  const screens = Grid.useBreakpoint();
  const headerCompact = !screens.md;
  const headerTight = !screens.sm;

  const [openKeys, setOpenKeys] = useState<string[]>([]);

  const pathOpenKeys = useMemo(() => {
    const p = location.pathname;
    const keys: string[] = [];
    if (p.startsWith("/app/cadastros")) keys.push("cadastros");
    if (p.startsWith("/app/estoque")) keys.push("estoque");
    if (p.startsWith("/app/financeiro")) keys.push("financeiro");
    if (p.startsWith("/app/relatorios")) keys.push("relatorios");
    if (p.startsWith("/app/admin")) keys.push("admin");
    return keys;
  }, [location.pathname]);

  useEffect(() => {
    setOpenKeys((prev) => {
      const next = new Set([...prev, ...pathOpenKeys]);
      return Array.from(next);
    });
  }, [pathOpenKeys]);

  const menuItems: MenuItem[] = useMemo(() => {
    const c = user?.capacidades;
    if (!c) return [];

    const items: MenuItem[] = [
      item("home", <Link to="/app">Início</Link>, <HomeOutlined />),
    ];

    if (c.painel) {
      items.push(
        item(
          "dashboard",
          <Link to="/app/dashboard">Painel</Link>,
          <DashboardOutlined />,
        ),
      );
    }

    if (c.dados_mestres) {
      items.push(
        item("cadastros", "Cadastros", <TagsOutlined />, [
          item("cat", <Link to="/app/cadastros/categorias">Categorias</Link>),
          item("sup", <Link to="/app/cadastros/fornecedores">Fornecedores</Link>),
          item("cust", <Link to="/app/cadastros/clientes">Clientes</Link>),
          item("prod", <Link to="/app/cadastros/produtos">Produtos</Link>),
        ]),
      );
    }

    const estChildren: MenuItem[] = [];
    if (c.estoque_leitura) {
      estChildren.push(item("bal", <Link to="/app/estoque/saldos">Saldos</Link>));
    }
    if (c.estoque_movimentacoes) {
      estChildren.push(
        item("ent", <Link to="/app/estoque/entradas-compra">Entrada de compra</Link>),
      );
    }
    if (c.estoque_leitura) {
      estChildren.push(item("sai", <Link to="/app/estoque/saidas">Saídas</Link>));
    }
    if (c.estoque_movimentacoes) {
      estChildren.push(item("mov", <Link to="/app/estoque/movimentos">Movimentos</Link>));
    }
    if (c.receitas_producao) {
      estChildren.push(item("rec", <Link to="/app/estoque/receitas">Receitas</Link>));
      estChildren.push(item("pr", <Link to="/app/estoque/producao">Produção</Link>));
    }
    if (c.estoque_leitura) {
      estChildren.push(
        item(
          "al-link",
          <Link to="/app/estoque/alertas">
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              Alertas
              {stockAlerts != null && stockAlerts > 0 ? (
                <Badge
                  count={stockAlerts > 99 ? 99 : stockAlerts}
                  overflowCount={99}
                  title="Itens abaixo do mínimo"
                />
              ) : null}
            </span>
          </Link>,
        ),
      );
    }
    if (estChildren.length) {
      items.push(item("estoque", "Estoque", <InboxOutlined />, estChildren));
    }

    const finChildren: MenuItem[] = [];
    if (c.financeiro) {
      finChildren.push(item("ap", <Link to="/app/financeiro/pagar">Contas a pagar</Link>));
      finChildren.push(item("ar", <Link to="/app/financeiro/receber">Contas a receber</Link>));
      finChildren.push(
        item("doc", <Link to="/app/financeiro/documentos">Documentos parcelados</Link>),
      );
      finChildren.push(item("cf", <Link to="/app/financeiro/fluxo-caixa">Fluxo de caixa</Link>));
      finChildren.push(
        item(
          "fa-link",
          <Link to="/app/financeiro/alertas">
            <span style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
              Alertas financeiros
              {financeOverdue != null && financeOverdue > 0 ? (
                <Badge
                  count={financeOverdue > 99 ? 99 : financeOverdue}
                  overflowCount={99}
                  title="Títulos vencidos (pagar + receber)"
                />
              ) : null}
            </span>
          </Link>,
        ),
      );
    }
    if (finChildren.length) {
      items.push(item("financeiro", "Financeiro", <DollarOutlined />, finChildren));
    }

    if (c.relatorios) {
      items.push(
        item(
          "relatorios",
          <Link to="/app/relatorios">Relatórios</Link>,
          <FileTextOutlined />,
        ),
      );
    }

    if (c.gerenciar_usuarios) {
      items.push(
        item("admin", "Administração", <TeamOutlined />, [
          item(
            "adm-users",
            <Link to="/app/admin/usuarios">Usuários e permissões</Link>,
          ),
        ]),
      );
    }

    return items;
  }, [user, stockAlerts, financeOverdue]);

  const selectedKeys = useMemo(() => {
    const p = location.pathname;
    if (p === "/app" || p === "/app/") return ["home"];
    if (p.startsWith("/app/dashboard")) return ["dashboard"];
    if (p.startsWith("/app/cadastros/categorias")) return ["cat"];
    if (p.startsWith("/app/cadastros/fornecedores")) return ["sup"];
    if (p.startsWith("/app/cadastros/clientes")) return ["cust"];
    if (p.startsWith("/app/cadastros/produtos")) return ["prod"];
    if (p.startsWith("/app/estoque/saldos")) return ["bal"];
    if (p.startsWith("/app/estoque/movimentos")) return ["mov"];
    if (p.startsWith("/app/estoque/receitas")) return ["rec"];
    if (p.startsWith("/app/estoque/producao")) return ["pr"];
    if (p.startsWith("/app/estoque/alertas")) return ["al-link"];
    if (p.startsWith("/app/financeiro/pagar")) return ["ap"];
    if (p.startsWith("/app/financeiro/receber")) return ["ar"];
    if (p.startsWith("/app/financeiro/documentos")) return ["doc"];
    if (p.startsWith("/app/financeiro/fluxo-caixa")) return ["cf"];
    if (p.startsWith("/app/financeiro/alertas")) return ["fa-link"];
    if (p.startsWith("/app/relatorios")) return ["relatorios"];
    if (p.startsWith("/app/admin/usuarios")) return ["adm-users"];
    return [];
  }, [location.pathname]);

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        breakpoint="lg"
        collapsedWidth={64}
        width={240}
        theme="dark"
        style={{ position: "sticky", top: 0, height: "100vh" }}
      >
        <div className="app-layout-sider-brand" title="Gestão Artesanal">
          <span className="app-layout-sider-brand-line">Gestão</span>
          <span className="app-layout-sider-brand-line">Artesanal</span>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedKeys}
          openKeys={openKeys}
          onOpenChange={(keys) => setOpenKeys(keys as string[])}
          items={menuItems}
          style={{ borderInlineEnd: "none" }}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: token.colorBgContainer,
            padding: headerCompact ? "0 12px" : "0 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            rowGap: 8,
            columnGap: 12,
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
            minHeight: 64,
            height: "auto",
            paddingTop: 8,
            paddingBottom: 8,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: headerTight ? 8 : 10,
              minWidth: 0,
              flex: headerTight ? "1 1 100%" : "0 1 auto",
            }}
          >
            <img
              src={logo}
              alt="Logo"
              style={{ height: headerTight ? 32 : 36, objectFit: "contain", flexShrink: 0 }}
            />
            {!headerTight ? (
              <span style={{ fontWeight: 600, whiteSpace: "nowrap" }}>Gestão Artesanal</span>
            ) : null}
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: headerTight ? 8 : 12,
              minWidth: 0,
              flex: headerTight ? "1 1 100%" : "0 1 auto",
              justifyContent: headerTight ? "space-between" : "flex-end",
              maxWidth: headerTight ? "100%" : undefined,
            }}
          >
            <CabecalhoNotificacoes stockAlertCount={stockAlerts} financeOverdueCount={financeOverdue} />
            <span
              style={{
                color: token.colorTextSecondary,
                flex: headerTight ? 1 : undefined,
                minWidth: headerTight ? 0 : undefined,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                fontSize: headerTight ? 13 : undefined,
              }}
              title={
                user?.username
                  ? `${user.username}${user.papel ? ` (${ROTULOS_PAPEL[user.papel]})` : ""}`
                  : undefined
              }
            >
              {user?.username}
              {user?.papel && !headerTight ? (
                <span style={{ marginLeft: 8, opacity: 0.85 }}>
                  ({ROTULOS_PAPEL[user.papel]})
                </span>
              ) : null}
              {user?.papel && headerTight ? (
                <span style={{ marginLeft: 6, opacity: 0.85 }}>
                  · {ROTULOS_PAPEL[user.papel]}
                </span>
              ) : null}
            </span>
            {headerTight ? (
              <Tooltip title="Sair">
                <Button type="default" icon={<LogoutOutlined />} onClick={() => logout()} />
              </Tooltip>
            ) : (
              <Button type="default" icon={<LogoutOutlined />} onClick={() => logout()}>
                Sair
              </Button>
            )}
          </div>
        </Header>
        <Content
          style={{
            margin: headerCompact ? 12 : 24,
            minHeight: 280,
            maxWidth: "100%",
            boxSizing: "border-box",
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
