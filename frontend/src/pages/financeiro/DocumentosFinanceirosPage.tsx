import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  DatePicker,
  Drawer,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { Link, useSearchParams } from "react-router-dom";
import { BarraPaginacao } from "../../components/BarraPaginacao";
import {
  FormularioParcelamento,
  type ValoresFormularioParcelamento,
} from "../../components/financeiro/FormularioParcelamento";
import { TabelaParcelas } from "../../components/financeiro/TabelaParcelas";
import { intervaloParaDias } from "../../components/financeiro/utilsParcelamento";
import { listarTodosClientes, listarTodosFornecedores } from "../../api/cadastro";
import {
  cancelarDocumentoFinanceiro,
  criarDocumentoFinanceiro,
  listarDocumentosFinanceiros,
  obterDocumentoFinanceiro,
  quitarParcelaDocumento,
} from "../../api/financeiro";
import type { Cliente, Fornecedor } from "../../types/cadastro";
import type {
  DocumentoFinanceiro,
  ParcelaDocumento,
  TipoDocumentoFinanceiro,
} from "../../types/financeiro";
import { todayLocal } from "../../utils/data";

const PAGE_SIZE = 20;

const ROTULO_TIPO: Record<TipoDocumentoFinanceiro, string> = {
  pagar: "A pagar",
  receber: "A receber",
};

const ROTULO_DOC_SIT: Record<string, string> = {
  aberto: "Em aberto",
  quitado: "Quitado",
  cancelado: "Cancelado",
};

const parcelamentoInicial: ValoresFormularioParcelamento = {
  valorTotal: "",
  numeroParcelas: 3,
  primeiraData: todayLocal(),
  intervalo: "mensal",
  intervaloDiasCustom: 30,
};

export function DocumentosFinanceirosPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [list, setList] = useState<DocumentoFinanceiro[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [filterTipo, setFilterTipo] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const [modalAberto, setModalAberto] = useState(false);
  const [tipoNovo, setTipoNovo] = useState<TipoDocumentoFinanceiro>("pagar");
  const [descricao, setDescricao] = useState("");
  const [fornecedorId, setFornecedorId] = useState<string>("");
  const [clienteId, setClienteId] = useState<string>("");
  const [observacoes, setObservacoes] = useState("");
  const [parcelamento, setParcelamento] = useState(parcelamentoInicial);
  const [fornecedores, setFornecedores] = useState<Fornecedor[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [salvando, setSalvando] = useState(false);

  const [detalhe, setDetalhe] = useState<DocumentoFinanceiro | null>(null);
  const [drawerAberto, setDrawerAberto] = useState(false);
  const [quitarModal, setQuitarModal] = useState<ParcelaDocumento | null>(null);
  const [valorBaixa, setValorBaixa] = useState("");
  const [dataBaixa, setDataBaixa] = useState(todayLocal());

  useEffect(() => {
    void Promise.all([listarTodosFornecedores(), listarTodosClientes()]).then(
      ([f, c]) => {
        setFornecedores(f);
        setClientes(c);
      },
    );
  }, []);

  /** Atalho vindo de Contas a pagar/receber: ?novo=pagar ou ?novo=receber */
  useEffect(() => {
    const novo = searchParams.get("novo");
    if (novo === "pagar" || novo === "receber") {
      setTipoNovo(novo);
      setModalAberto(true);
      const next = new URLSearchParams(searchParams);
      next.delete("novo");
      setSearchParams(next, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarDocumentosFinanceiros({
        page,
        tipo: filterTipo || undefined,
        ordering: "-data_emissao",
      });
      setList(data.resultados);
      setCount(data.total);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar documentos");
    } finally {
      setLoading(false);
    }
  }, [page, filterTipo]);

  useEffect(() => {
    void load();
  }, [load]);

  const abrirDetalhe = async (id: number) => {
    setErr(null);
    try {
      const doc = await obterDocumentoFinanceiro(id);
      setDetalhe(doc);
      setDrawerAberto(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao carregar documento");
    }
  };

  const criarDocumento = async () => {
    const valor = Number(String(parcelamento.valorTotal).replace(",", "."));
    if (!descricao.trim() || !parcelamento.primeiraData || !Number.isFinite(valor) || valor <= 0) {
      setErr("Preencha descrição, valor e data da 1ª parcela.");
      return;
    }
    if (tipoNovo === "pagar" && !fornecedorId) {
      setErr("Selecione o fornecedor.");
      return;
    }
    if (tipoNovo === "receber" && !clienteId) {
      setErr("Selecione o cliente.");
      return;
    }
    setSalvando(true);
    setErr(null);
    try {
      const doc = await criarDocumentoFinanceiro({
        tipo: tipoNovo,
        fornecedor: tipoNovo === "pagar" ? Number(fornecedorId) : null,
        cliente: tipoNovo === "receber" ? Number(clienteId) : null,
        descricao: descricao.trim(),
        valor_total: valor.toFixed(2),
        numero_parcelas: parcelamento.numeroParcelas,
        primeira_data: parcelamento.primeiraData,
        intervalo_dias: intervaloParaDias(
          parcelamento.intervalo,
          parcelamento.intervaloDiasCustom,
        ),
        observacoes: observacoes.trim(),
      });
      setModalAberto(false);
      setDescricao("");
      setFornecedorId("");
      setClienteId("");
      setObservacoes("");
      setParcelamento(parcelamentoInicial);
      await load();
      await abrirDetalhe(doc.id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao criar documento");
    } finally {
      setSalvando(false);
    }
  };

  const confirmarBaixa = async () => {
    if (!detalhe || !quitarModal) return;
    const v = Number(String(valorBaixa).replace(",", "."));
    if (!Number.isFinite(v) || v <= 0) {
      setErr("Informe um valor de baixa válido.");
      return;
    }
    if (!dataBaixa) {
      setErr("Informe a data da baixa.");
      return;
    }
    setSalvando(true);
    setErr(null);
    try {
      const atualizado = await quitarParcelaDocumento(detalhe.id, {
        parcela_id: quitarModal.id,
        valor: v.toFixed(2),
        data_pagamento: dataBaixa,
      });
      setDetalhe(atualizado);
      setQuitarModal(null);
      setValorBaixa("");
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao registrar baixa");
    } finally {
      setSalvando(false);
    }
  };

  const cancelarDoc = async () => {
    if (!detalhe) return;
    setSalvando(true);
    setErr(null);
    try {
      const atualizado = await cancelarDocumentoFinanceiro(detalhe.id);
      setDetalhe(atualizado);
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao cancelar documento");
    } finally {
      setSalvando(false);
    }
  };

  const columns: ColumnsType<DocumentoFinanceiro> = useMemo(
    () => [
      { title: "Emissão", dataIndex: "data_emissao", key: "data_emissao", width: 110 },
      {
        title: "Tipo",
        dataIndex: "tipo",
        key: "tipo",
        width: 100,
        render: (t: TipoDocumentoFinanceiro) => ROTULO_TIPO[t],
      },
      { title: "Descrição", dataIndex: "descricao", key: "descricao" },
      {
        title: "Contraparte",
        key: "contraparte",
        render: (_, row) =>
          row.tipo === "pagar" ? row.nome_fornecedor ?? "—" : row.nome_cliente ?? "—",
      },
      { title: "Valor total", dataIndex: "valor_total", key: "valor_total", width: 110 },
      {
        title: "Parcelas",
        key: "parcelas",
        width: 90,
        render: (_, row) => row.numero_parcelas,
      },
      {
        title: "Situação",
        dataIndex: "situacao",
        key: "situacao",
        width: 110,
        render: (s: string) => <Tag>{ROTULO_DOC_SIT[s] ?? s}</Tag>,
      },
      {
        title: "",
        key: "acao",
        width: 90,
        render: (_, row) => (
          <Button type="link" size="small" onClick={() => void abrirDetalhe(row.id)}>
            Detalhes
          </Button>
        ),
      },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Space style={{ justifyContent: "space-between", width: "100%" }} wrap>
        <Typography.Title level={3} style={{ margin: 0 }}>
          Documentos parcelados
        </Typography.Title>
        <Button type="primary" onClick={() => setModalAberto(true)}>
          Novo documento
        </Button>
      </Space>

      <Typography.Paragraph type="secondary" style={{ margin: 0 }}>
        Agrupe várias parcelas em um único documento. As parcelas individuais também aparecem em{" "}
        <Link to="/app/financeiro/pagar">Contas a pagar</Link> e{" "}
        <Link to="/app/financeiro/receber">Contas a receber</Link>.
      </Typography.Paragraph>

      {err ? <Alert type="error" message={err} showIcon closable onClose={() => setErr(null)} /> : null}

      <Card size="small" title="Filtros">
        <Select
          placeholder="Tipo"
          allowClear
          style={{ width: 180 }}
          value={filterTipo || undefined}
          onChange={(v) => {
            setFilterTipo(v ?? "");
            setPage(1);
          }}
          options={[
            { value: "pagar", label: "A pagar" },
            { value: "receber", label: "A receber" },
          ]}
        />
      </Card>

      <Spin spinning={loading}>
        <Table rowKey="id" size="small" columns={columns} dataSource={list} pagination={false} />
        <BarraPaginacao
          page={page}
          pageSize={PAGE_SIZE}
          totalCount={count}
          onPageChange={setPage}
        />
      </Spin>

      <Modal
        title="Novo documento parcelado"
        open={modalAberto}
        onCancel={() => setModalAberto(false)}
        onOk={() => void criarDocumento()}
        confirmLoading={salvando}
        okText="Criar documento"
        width={720}
        destroyOnClose
      >
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Form layout="vertical">
            <Form.Item label="Tipo" required>
              <Select
                value={tipoNovo}
                onChange={setTipoNovo}
                options={[
                  { value: "pagar", label: "Contas a pagar" },
                  { value: "receber", label: "Contas a receber" },
                ]}
              />
            </Form.Item>
            {tipoNovo === "pagar" ? (
              <Form.Item label="Fornecedor" required>
                <Select
                  showSearch
                  optionFilterProp="label"
                  value={fornecedorId || undefined}
                  onChange={setFornecedorId}
                  options={fornecedores.map((f) => ({ value: String(f.id), label: f.nome }))}
                />
              </Form.Item>
            ) : (
              <Form.Item label="Cliente" required>
                <Select
                  showSearch
                  optionFilterProp="label"
                  value={clienteId || undefined}
                  onChange={setClienteId}
                  options={clientes.map((c) => ({ value: String(c.id), label: c.nome }))}
                />
              </Form.Item>
            )}
            <Form.Item label="Descrição" required>
              <Input value={descricao} onChange={(e) => setDescricao(e.target.value)} />
            </Form.Item>
            <Form.Item label="Observações">
              <Input.TextArea
                rows={2}
                value={observacoes}
                onChange={(e) => setObservacoes(e.target.value)}
              />
            </Form.Item>
          </Form>
          <FormularioParcelamento
            valores={parcelamento}
            onChange={(patch) => setParcelamento((prev) => ({ ...prev, ...patch }))}
          />
        </Space>
      </Modal>

      <Drawer
        title={detalhe ? `Documento #${detalhe.id} — ${detalhe.descricao}` : "Documento"}
        width={720}
        open={drawerAberto}
        onClose={() => {
          setDrawerAberto(false);
          setDetalhe(null);
        }}
        extra={
          detalhe && detalhe.situacao === "aberto" ? (
            <Button danger loading={salvando} onClick={() => void cancelarDoc()}>
              Cancelar documento
            </Button>
          ) : null
        }
      >
        {detalhe ? (
          <Space direction="vertical" size="large" style={{ width: "100%" }}>
            <Space wrap>
              <Tag>{ROTULO_TIPO[detalhe.tipo]}</Tag>
              <Tag>{ROTULO_DOC_SIT[detalhe.situacao]}</Tag>
              <Typography.Text>
                Total: <strong>R$ {detalhe.valor_total}</strong> · {detalhe.numero_parcelas}{" "}
                parcela(s)
              </Typography.Text>
            </Space>
            <TabelaParcelas
              parcelas={detalhe.parcelas}
              tipo={detalhe.tipo}
              documentoCancelado={detalhe.situacao === "cancelado"}
              onQuitar={(p) => {
                setQuitarModal(p);
                setValorBaixa(p.saldo_restante);
                setDataBaixa(todayLocal());
              }}
            />
          </Space>
        ) : null}
      </Drawer>

      <Modal
        title="Registrar baixa na parcela"
        open={quitarModal != null}
        onCancel={() => setQuitarModal(null)}
        onOk={() => void confirmarBaixa()}
        confirmLoading={salvando}
        okText="Confirmar baixa"
      >
        <Form layout="vertical">
          <Form.Item label="Valor (R$)">
            <Input value={valorBaixa} onChange={(e) => setValorBaixa(e.target.value)} />
          </Form.Item>
          <Form.Item label="Data">
            <DatePicker
              style={{ width: "100%" }}
              format="YYYY-MM-DD"
              value={dataBaixa ? dayjs(dataBaixa) : null}
              onChange={(_, s) => setDataBaixa(typeof s === "string" ? s : "")}
            />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
