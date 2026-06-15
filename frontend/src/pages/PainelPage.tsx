import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  InputNumber,
  Row,
  Segmented,
  Space,
  Spin,
  Statistic,
  Typography,
} from "antd";
import { Link, useSearchParams } from "react-router-dom";
import { ReloadOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { obterFluxoCaixa } from "../api/financeiro";
import { buscarResumoNotificacoes } from "../api/notificacoes";
import {
  buscarRelatorioEnvelhecimentoFinanceiro,
  buscarRelatorioEstoquePorCategoria,
  buscarRelatorioFluxoMensal,
} from "../api/relatorios";
import { CartaoEstatistica } from "../components/CartaoEstatistica";
import { CartaoGrafico } from "../components/painel/CartaoGrafico";
import { GraficoAging } from "../components/painel/GraficoAging";
import { GraficoEstoqueCategorias } from "../components/painel/GraficoEstoqueCategorias";
import { GraficoFluxoMensal } from "../components/painel/GraficoFluxoMensal";
import { GraficoTopProdutos } from "../components/painel/GraficoTopProdutos";
import { useAutenticacao } from "../hooks/useAutenticacao";
import { useToast } from "../hooks/useToast";
import type { RespostaFluxoCaixa } from "../types/financeiro";
import type { ResumoNotificacoes } from "../types/notificacoes";
import type {
  RelatorioEnvelhecimentoFinanceiro,
  RelatorioEstoquePorCategoria,
  RelatorioFluxoMensal,
} from "../types/relatorios";

const cores = {
  success: "#52c41a",
  warning: "#faad14",
  error: "#ff4d4f",
  info: "#1677ff",
};

const OPCOES_MESES = [
  { label: "3 meses", value: 3 },
  { label: "6 meses", value: 6 },
  { label: "12 meses", value: 12 },
  { label: "24 meses", value: 24 },
] as const;

function primeiroDiaMesLocal(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
}

function hojeLocal(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate(),
  ).padStart(2, "0")}`;
}

export function PainelPage() {
  const { showToast } = useToast();
  const { user } = useAutenticacao();
  const [searchParams, setSearchParams] = useSearchParams();

  const mesesURL = Number(searchParams.get("meses"));
  const mesesInicial = OPCOES_MESES.some((o) => o.value === mesesURL) ? mesesURL : 12;

  const [meses, setMeses] = useState<number>(mesesInicial);
  const [daysAhead, setDaysAhead] = useState(7);
  const [summary, setSummary] = useState<ResumoNotificacoes | null>(null);
  const [cashFlow, setCashFlow] = useState<RespostaFluxoCaixa | null>(null);
  const [fluxoMensal, setFluxoMensal] = useState<RelatorioFluxoMensal | null>(null);
  const [aging, setAging] = useState<RelatorioEnvelhecimentoFinanceiro | null>(null);
  const [estoqueCategorias, setEstoqueCategorias] =
    useState<RelatorioEstoquePorCategoria | null>(null);

  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);

  const periodo = useMemo(() => {
    const from = dateRange ? dateRange[0] : primeiroDiaMesLocal();
    const to = dateRange ? dateRange[1] : hojeLocal();
    return { from, to };
  }, [dateRange]);

  const podeVerRelatorio = user?.capacidades.relatorios ?? false;
  const podeVerFinanceiro = user?.capacidades.financeiro ?? false;
  const podeVerEstoque = user?.capacidades.estoque_leitura ?? false;

  const carregar = useCallback(
    async (opts?: { silent?: boolean }) => {
      setLoading(true);
      setErr(null);

      const { from, to } = periodo;

      try {
        const [sumResult, cfResult, fluxoResult, agingResult, categoriasResult] =
          await Promise.allSettled([
            buscarResumoNotificacoes(daysAhead, 10, from, to),
            obterFluxoCaixa(from, to),
            podeVerRelatorio
              ? buscarRelatorioFluxoMensal(meses)
              : Promise.resolve(null),
            podeVerRelatorio
              ? buscarRelatorioEnvelhecimentoFinanceiro()
              : Promise.resolve(null),
            podeVerRelatorio
              ? buscarRelatorioEstoquePorCategoria()
              : Promise.resolve(null),
          ]);

        if (sumResult.status === "fulfilled") {
          setSummary(sumResult.value);
        } else {
          setSummary(null);
          throw sumResult.reason;
        }

        setCashFlow(cfResult.status === "fulfilled" ? cfResult.value : null);
        setFluxoMensal(
          fluxoResult.status === "fulfilled" ? (fluxoResult.value as RelatorioFluxoMensal | null) : null,
        );
        setAging(
          agingResult.status === "fulfilled"
            ? (agingResult.value as RelatorioEnvelhecimentoFinanceiro | null)
            : null,
        );
        setEstoqueCategorias(
          categoriasResult.status === "fulfilled"
            ? (categoriasResult.value as RelatorioEstoquePorCategoria | null)
            : null,
        );

        if (!opts?.silent) {
          showToast("Painel atualizado", "success");
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Erro ao carregar o painel";
        setErr(msg);
        showToast(msg, "error");
      } finally {
        setLoading(false);
      }
    },
    [daysAhead, meses, periodo, podeVerRelatorio, showToast],
  );

  useEffect(() => {
    void carregar({ silent: true });
  }, [carregar]);

  const trocarMeses = (valor: number) => {
    setMeses(valor);
    const next = new URLSearchParams(searchParams);
    if (valor === 12) next.delete("meses");
    else next.set("meses", String(valor));
    setSearchParams(next, { replace: true });
  };

  const financeOverdueTotal = summary
    ? summary.financeiro.vencidos.contagem_pagar +
      summary.financeiro.vencidos.contagem_receber
    : 0;

  const vendas = summary?.vendas_por_produto;

  return (
    <Space direction="vertical" size="large" style={{ width: "100%", padding: 24 }}>
      <Row justify="space-between" align="middle" gutter={[16, 16]}>
        <Col flex="1">
          <Typography.Title level={3} style={{ marginBottom: 0 }}>
            Painel
          </Typography.Title>
          <Typography.Text type="secondary">Visão geral operacional e financeira</Typography.Text>
          {summary ? (
            <Typography.Text type="secondary" style={{ fontSize: 12, display: "block" }}>
              Última atualização: {new Date(summary.gerado_em).toLocaleString("pt-BR")}
            </Typography.Text>
          ) : null}
        </Col>
        <Col>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => void carregar({ silent: false })}
            loading={loading}
          >
            Atualizar dados
          </Button>
        </Col>
      </Row>

      <Card size="small" title="Parâmetros">
        <Space wrap align="center">
          <Typography.Text type="secondary">Dias à frente (financeiro)</Typography.Text>
          <InputNumber
            min={0}
            max={365}
            value={daysAhead}
            onChange={(v) => setDaysAhead(Number(v) || 0)}
          />
          <Typography.Text type="secondary">Período (KPIs)</Typography.Text>
          <DatePicker.RangePicker
            format="DD/MM/YYYY"
            value={[dayjs(periodo.from), dayjs(periodo.to)]}
            onChange={(dates) => {
              const [start, end] = dates ?? [];
              if (start && end) {
                setDateRange([start.format("YYYY-MM-DD"), end.format("YYYY-MM-DD")]);
              } else {
                setDateRange(null);
              }
            }}
          />
          {podeVerRelatorio ? (
            <>
              <Typography.Text type="secondary">Fluxo mensal</Typography.Text>
              <Segmented
                value={meses}
                onChange={(v) => trocarMeses(Number(v))}
                options={OPCOES_MESES.map((o) => ({ label: o.label, value: o.value }))}
              />
            </>
          ) : null}
        </Space>
      </Card>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading && !summary}>
        {summary ? (
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} lg={6}>
              <CartaoEstatistica
                title="Estoque crítico"
                value={summary.estoque_abaixo_minimo.quantidade}
                color={cores.warning}
                subtitle="abaixo do mínimo"
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <CartaoEstatistica
                title="Títulos vencidos"
                value={financeOverdueTotal}
                color={financeOverdueTotal > 0 ? cores.error : cores.success}
                subtitle="pagar + receber"
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <CartaoEstatistica
                title="Contas a pagar"
                value={summary.financeiro.vencidos.contagem_pagar}
                color={cores.error}
                subtitle="em aberto"
              />
            </Col>
            <Col xs={24} sm={12} lg={6}>
              <CartaoEstatistica
                title="Contas a receber"
                value={summary.financeiro.vencidos.contagem_receber}
                color={cores.info}
                subtitle="em aberto"
              />
            </Col>
          </Row>
        ) : null}
      </Spin>

      {cashFlow ? (
        <Card
          title="Fluxo de caixa do período"
          extra={
            <Typography.Text type="secondary">
              {cashFlow.from} → {cashFlow.to}
            </Typography.Text>
          }
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Statistic
                title="Entradas"
                value={cashFlow.inflows}
                precision={2}
                prefix="R$"
                valueStyle={{ color: cores.success }}
              />
            </Col>
            <Col xs={24} md={8}>
              <Statistic
                title="Saídas"
                value={cashFlow.outflows}
                precision={2}
                prefix="R$"
                valueStyle={{ color: cores.error }}
              />
            </Col>
            <Col xs={24} md={8}>
              <Statistic
                title="Líquido"
                value={cashFlow.net}
                precision={2}
                prefix="R$"
                valueStyle={{
                  color: Number(cashFlow.net) >= 0 ? cores.success : cores.error,
                }}
              />
            </Col>
          </Row>
          {podeVerFinanceiro ? (
            <Link to="/app/financeiro/fluxo-caixa">
              <Typography.Link>Ver fluxo com período customizado →</Typography.Link>
            </Link>
          ) : null}
        </Card>
      ) : null}

      {/* Linha 1 dos gráficos: fluxo mensal + aging */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <CartaoGrafico
            titulo="Fluxo de caixa mensal"
            descricao={`Entradas, saídas e líquido nos últimos ${meses} meses (lançamentos quitados).`}
            carregando={loading && !fluxoMensal}
            vazio={!fluxoMensal || fluxoMensal.resultados.length === 0}
            textoVazio={podeVerRelatorio ? "Sem dados no período" : "Sem permissão para visualizar"}
          >
            {fluxoMensal ? <GraficoFluxoMensal dados={fluxoMensal.resultados} /> : null}
          </CartaoGrafico>
        </Col>
        <Col xs={24} lg={10}>
          <CartaoGrafico
            titulo="Envelhecimento financeiro"
            descricao="Distribuição de títulos a pagar e a receber por faixa de vencimento."
            carregando={loading && !aging}
            vazio={!aging}
            textoVazio={
              podeVerRelatorio ? "Sem títulos em aberto" : "Sem permissão para visualizar"
            }
          >
            {aging ? <GraficoAging dados={aging} /> : null}
          </CartaoGrafico>
        </Col>
      </Row>

      {/* Linha 2: top produtos + estoque por categoria */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <CartaoGrafico
            titulo="Top 5 produtos por lucro"
            descricao="Calculado a partir das linhas de contas a receber emitidas no período."
            carregando={loading && !vendas}
            vazio={!vendas || vendas.top_produtos.length === 0}
            textoVazio="Sem vendas no período"
            extra={
              podeVerRelatorio && vendas ? (
                <Link to="/app/relatorios/financeiro/receita-produto">
                  <Typography.Link>Relatório completo →</Typography.Link>
                </Link>
              ) : null
            }
          >
            {vendas ? <GraficoTopProdutos dados={vendas.top_produtos} top={5} /> : null}
          </CartaoGrafico>
        </Col>
        <Col xs={24} lg={10}>
          <CartaoGrafico
            titulo="Estoque por categoria"
            descricao="Valor estimado de estoque (saldo × custo unitário) agrupado por categoria."
            carregando={loading && !estoqueCategorias}
            vazio={!estoqueCategorias || estoqueCategorias.resultados.length === 0}
            textoVazio={
              podeVerRelatorio ? "Sem saldos por categoria" : "Sem permissão para visualizar"
            }
            extra={
              estoqueCategorias ? (
                <Typography.Text type="secondary">
                  Total: R$ {estoqueCategorias.valor_total}
                </Typography.Text>
              ) : null
            }
          >
            {estoqueCategorias ? (
              <GraficoEstoqueCategorias dados={estoqueCategorias.resultados} />
            ) : null}
          </CartaoGrafico>
        </Col>
      </Row>

      {summary ? (
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card title="Atalhos — estoque">
              <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
                {summary.estoque_abaixo_minimo.quantidade} produto(s) com saldo igual ou inferior
                ao mínimo configurado.
              </Typography.Paragraph>
              <Space wrap>
                {podeVerEstoque ? (
                  <Link to="/app/estoque/alertas">
                    <Button type="primary">Alertas de estoque</Button>
                  </Link>
                ) : null}
              </Space>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card title="Atalhos — financeiro">
              <Typography.Paragraph style={{ marginBottom: 12 }}>
                <Typography.Text type="secondary">
                  A vencer até {summary.financeiro.ate}
                </Typography.Text>
                <br />
                <strong>
                  {summary.financeiro.a_vencer.contagem_pagar} pagar ·{" "}
                  {summary.financeiro.a_vencer.contagem_receber} receber
                </strong>
              </Typography.Paragraph>
              {podeVerFinanceiro ? (
                <Space wrap>
                  <Link to="/app/financeiro/alertas">
                    <Button>Alertas</Button>
                  </Link>
                  <Link to="/app/financeiro/pagar">
                    <Button>A pagar</Button>
                  </Link>
                  <Link to="/app/financeiro/receber">
                    <Button>A receber</Button>
                  </Link>
                </Space>
              ) : null}
            </Card>
          </Col>
        </Row>
      ) : null}
    </Space>
  );
}
