import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Space, Spin, Table, Typography } from "antd";
import { BarraPaginacao } from "../../components/BarraPaginacao";
import { colunasContaReceber } from "../../components/financeiro/contasReceber/colunasContaReceber";
import { FiltrosContaReceber } from "../../components/financeiro/contasReceber/FiltrosContaReceber";
import { FormularioContaReceber } from "../../components/financeiro/contasReceber/FormularioContaReceber";
import {
  isPrecoUnitarioVazio,
  mapApiLineToForm,
  parseDecimal,
  precoCatalogoParaLinha,
  totalLinha,
} from "../../components/financeiro/contasReceber/helpers";
import {
  formContaReceberVazio,
  linhaVazia,
  type FormContaReceber,
  type LinhaFormContaReceber,
} from "../../components/financeiro/contasReceber/types";
import { listarTodosClientes, listarTodosProdutos } from "../../api/cadastro";
import {
  criarContaReceber,
  excluirContaReceber,
  listarContasReceber,
  atualizarContaReceber,
} from "../../api/financeiro";
import {
  coerceProductUnitCode,
  compatibleUnitsForProduct,
  DEFAULT_PRODUCT_UNIT,
} from "../../constants/unidades";
import type { Cliente, Produto } from "../../types/cadastro";
import type { ContaReceber } from "../../types/financeiro";

const PAGE_SIZE = 20;

export function ContasReceberPage() {
  const [list, setList] = useState<ContaReceber[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [filterSituacao, setFilterStatus] = useState<string>("");
  const [filterParcelado, setFilterParcelado] = useState<string>("");
  const [filterCliente, setFilterCliente] = useState<string>("");
  const [dueFrom, setDueFrom] = useState("");
  const [dueTo, setDueTo] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [customers, setClientes] = useState<Cliente[]>([]);
  const [products, setProdutos] = useState<Produto[]>([]);
  const [form, setForm] = useState<FormContaReceber>(formContaReceberVazio);
  const [editing, setEditing] = useState<ContaReceber | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void listarTodosClientes().then(setClientes).catch(() => {});
    void listarTodosProdutos({}).then(setProdutos).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const data = await listarContasReceber({
        page,
        search: search || undefined,
        situacao: filterSituacao || undefined,
        cliente: filterCliente || undefined,
        due_from: dueFrom || undefined,
        due_to: dueTo || undefined,
        documento_parcelado:
          filterParcelado === "sim" ? true : filterParcelado === "nao" ? false : undefined,
        ordering: "due_date",
      });
      setList(data.resultados);
      setCount(data.total);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao listar");
    } finally {
      setLoading(false);
    }
  }, [page, search, filterSituacao, filterParcelado, filterCliente, dueFrom, dueTo]);

  useEffect(() => {
    void load();
  }, [load]);

  const linesTotal = useMemo(
    () =>
      form.linhas.reduce(
        (s, ln) => s + totalLinha(ln.quantidade, ln.preco_unitario, ln.desconto),
        0,
      ),
    [form.linhas],
  );

  const buildPayload = (): Record<string, unknown> => {
    const cliente = form.cliente === "" ? null : Number(form.cliente);
    const lines = form.linhas
      .filter((ln) => ln.produto.trim())
      .map((ln) => ({
        produto: Number(ln.produto),
        quantidade: ln.quantidade.trim(),
        unidade: ln.unidade,
        preco_unitario: ln.preco_unitario.trim(),
        desconto: ln.desconto.trim() || "0",
      }));
    if (!lines.length) {
      throw new Error("Inclua ao menos uma linha com produto.");
    }
    for (let i = 0; i < lines.length; i++) {
      const ln = lines[i];
      const q = parseDecimal(String(ln.quantidade));
      const up = parseDecimal(String(ln.preco_unitario));
      const disc = parseDecimal(String(ln.desconto ?? "0")) ?? 0;
      if (q === null || q <= 0) {
        throw new Error(`Linha ${i + 1}: quantidade deve ser maior que zero.`);
      }
      if (up === null || up <= 0) {
        throw new Error(`Linha ${i + 1}: preço unitário deve ser maior que zero.`);
      }
      if (disc < 0) {
        throw new Error(`Linha ${i + 1}: desconto não pode ser negativo.`);
      }
      if (q * up - disc < -0.0001) {
        throw new Error(`Linha ${i + 1}: total da linha não pode ser negativo.`);
      }
    }
    const payload: Record<string, unknown> = {
      cliente,
      descricao: form.descricao.trim(),
      data_emissao: form.data_emissao,
      vencimento: form.vencimento,
      situacao: form.situacao,
      observacoes: form.observacoes.trim(),
      linhas: lines,
    };
    if (form.situacao === "recebido") {
      if (!form.recebido_em) {
        throw new Error("Informe a data efetiva do recebimento ao marcar como recebido.");
      }
      payload.recebido_em = form.recebido_em;
    }
    return payload;
  };

  const submitForm = async () => {
    if (!form.descricao.trim() || !form.vencimento) {
      setErr("Preencha descrição e vencimento.");
      return;
    }
    setSaving(true);
    setErr(null);
    try {
      const payload = buildPayload();
      if (editing) {
        await atualizarContaReceber(editing.id, payload);
      } else {
        await criarContaReceber(payload);
      }
      setForm(formContaReceberVazio());
      setEditing(null);
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (row: ContaReceber) => {
    setEditing(row);
    const lines =
      row.linhas && row.linhas.length > 0 ? row.linhas.map(mapApiLineToForm) : [linhaVazia()];
    setForm({
      cliente: row.cliente != null ? String(row.cliente) : "",
      descricao: row.descricao,
      data_emissao: row.data_emissao ?? formContaReceberVazio().data_emissao,
      vencimento: row.vencimento,
      situacao: row.situacao,
      recebido_em: row.recebido_em ?? "",
      observacoes: row.observacoes,
      linhas: lines,
    });
  };

  const cancelForm = () => {
    setEditing(null);
    setForm(formContaReceberVazio());
  };

  const handleDelete = async (row: ContaReceber) => {
    setErr(null);
    try {
      await excluirContaReceber(row.id);
      if (editing?.id === row.id) cancelForm();
      await load();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Erro ao excluir");
    }
  };

  const updateLine = (idx: number, patch: Partial<LinhaFormContaReceber>) => {
    setForm((f) => {
      const linhas = [...f.linhas];
      const cur = { ...linhas[idx], ...patch };
      if (patch.produto != null) {
        const p = products.find((x) => String(x.id) === cur.produto);
        if (p) {
          const u = coerceProductUnitCode(p.unidade);
          cur.unidade = compatibleUnitsForProduct(u).includes(cur.unidade)
            ? cur.unidade
            : (compatibleUnitsForProduct(u)[0] ?? DEFAULT_PRODUCT_UNIT);
          const catalog = precoCatalogoParaLinha(p);
          if (catalog != null && isPrecoUnitarioVazio(cur.preco_unitario)) {
            cur.preco_unitario = catalog;
          }
        }
      }
      linhas[idx] = cur;
      return { ...f, linhas };
    });
  };

  const addLine = () => setForm((f) => ({ ...f, linhas: [...f.linhas, linhaVazia()] }));
  const removeLine = (idx: number) =>
    setForm((f) => ({
      ...f,
      linhas: f.linhas.length > 1 ? f.linhas.filter((_, i) => i !== idx) : f.linhas,
    }));

  const aplicarPrecoCatalogo = (idx: number) => {
    const ln = form.linhas[idx];
    const p = products.find((x) => String(x.id) === ln.produto);
    if (!p) return;
    const catalog = precoCatalogoParaLinha(p);
    if (catalog != null) {
      updateLine(idx, { preco_unitario: catalog });
    }
  };

  const columns = useMemo(
    () =>
      colunasContaReceber({
        onEdit: startEdit,
        onDelete: (row) => void handleDelete(row),
      }),
    [],
  );

  const buscar = () => {
    setPage(1);
    setSearch(searchInput.trim());
  };

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Contas a receber
      </Typography.Title>

      <FiltrosContaReceber
        searchInput={searchInput}
        onSearchInputChange={setSearchInput}
        filterSituacao={filterSituacao}
        onFilterSituacaoChange={(v) => {
          setFilterStatus(v);
          setPage(1);
        }}
        filterParcelado={filterParcelado}
        onFilterParceladoChange={(v) => {
          setFilterParcelado(v);
          setPage(1);
        }}
        filterCliente={filterCliente}
        onFilterClienteChange={(v) => {
          setFilterCliente(v);
          setPage(1);
        }}
        dueFrom={dueFrom}
        onDueFromChange={(v) => {
          setDueFrom(v);
          setPage(1);
        }}
        dueTo={dueTo}
        onDueToChange={(v) => {
          setDueTo(v);
          setPage(1);
        }}
        customers={customers}
        onBuscar={buscar}
      />

      <FormularioContaReceber
        form={form}
        editing={editing}
        saving={saving}
        customers={customers}
        products={products}
        linesTotal={linesTotal}
        onFormChange={setForm}
        onSubmit={() => void submitForm()}
        onCancel={cancelForm}
        onUpdateLine={updateLine}
        onAddLine={addLine}
        onRemoveLine={removeLine}
        onAplicarPrecoCatalogo={aplicarPrecoCatalogo}
      />

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading}>
        <Table<ContaReceber>
          rowKey="id"
          columns={columns}
          dataSource={list}
          pagination={false}
          scroll={{ x: true }}
        />
        <BarraPaginacao page={page} totalCount={count} pageSize={PAGE_SIZE} onPageChange={setPage} />
      </Spin>
    </Space>
  );
}
