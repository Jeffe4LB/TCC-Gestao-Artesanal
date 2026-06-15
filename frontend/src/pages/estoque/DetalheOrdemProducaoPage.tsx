import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Alert, Button, Descriptions, Popconfirm, Space, Spin, Table, Typography } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { cancelarOrdemProducao, obterOrdemProducao } from "../../api/estoque";
import type { OrdemProducao } from "../../types/estoque";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityDisplay } from "../../utils/exibicaoQuantidade";

export function DetalheOrdemProducaoPage() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<OrdemProducao | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelando, setCancelando] = useState(false);

  useEffect(() => {
    if (!id) {
      setErr("ID inválido");
      setLoading(false);
      return;
    }
    let cancelled = false;
    void (async () => {
      setErr(null);
      setLoading(true);
      try {
        const data = await obterOrdemProducao(Number(id));
        if (!cancelled) setRun(data);
      } catch (e) {
        if (!cancelled) setErr(e instanceof Error ? e.message : "Erro ao carregar");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const handleCancelar = async () => {
    if (!run) return;
    setCancelando(true);
    setErr(null);
    try {
      const atualizado = await cancelarOrdemProducao(run.id);
      setRun(atualizado);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao cancelar produção");
    } finally {
      setCancelando(false);
    }
  };

  const lineColumns: ColumnsType<OrdemProducao["linhas"][number]> = [
    { title: "Código (SKU)", dataIndex: "codigo_insumo", key: "codigo_insumo" },
    { title: "Insumo", dataIndex: "nome_insumo", key: "nome_insumo" },
    {
      title: "Qtd consumida",
      dataIndex: "quantidade_consumida",
      key: "quantidade_consumida",
      render: (v: string) => formatQuantityDisplay(v),
    },
  ];

  if (loading) {
    return (
      <div style={{ padding: 48, textAlign: "center" }}>
        <Spin />
      </div>
    );
  }
  if (err && !run) {
    return <Alert type="error" message={err} showIcon />;
  }
  if (!run) {
    return <Alert type="error" message="Não encontrado" showIcon />;
  }

  return (
    <div>
      <Space style={{ marginBottom: 16 }} wrap>
        <Link to="/app/estoque/producao">
          <Button type="link" icon={<ArrowLeftOutlined />} style={{ paddingLeft: 0 }}>
            Voltar à lista
          </Button>
        </Link>
        {!run.cancelada_em ? (
          <Popconfirm
            title="Cancelar esta produção?"
            description="O estoque será estornado. O registro permanece no histórico."
            okText="Cancelar produção"
            cancelText="Voltar"
            okButtonProps={{ danger: true }}
            onConfirm={() => void handleCancelar()}
          >
            <Button danger loading={cancelando}>
              Cancelar produção
            </Button>
          </Popconfirm>
        ) : null}
      </Space>

      {run.cancelada_em ? (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message={`Produção cancelada em ${new Date(run.cancelada_em).toLocaleString()}`}
        />
      ) : null}

      {err ? <Alert type="error" message={err} showIcon style={{ marginBottom: 16 }} /> : null}

      <Typography.Title level={3}>Produção #{run.id}</Typography.Title>
      <Descriptions bordered column={1} size="small" style={{ marginBottom: 24, maxWidth: 560 }}>
        <Descriptions.Item label="Produto">
          {run.codigo_produto} — {run.nome_produto}
        </Descriptions.Item>
        <Descriptions.Item label="Quantidade produzida">
          {formatQuantityDisplay(run.quantidade_produzida)}
        </Descriptions.Item>
        <Descriptions.Item label="Situação">
          {run.cancelada_em ? "Cancelada" : "Ativa"}
        </Descriptions.Item>
        <Descriptions.Item label="Registrada em">
          {new Date(run.criado_em).toLocaleString()}
        </Descriptions.Item>
        {run.cancelada_em ? (
          <Descriptions.Item label="Cancelada em">
            {new Date(run.cancelada_em).toLocaleString()}
          </Descriptions.Item>
        ) : null}
        {run.observacoes ? <Descriptions.Item label="Obs.">{run.observacoes}</Descriptions.Item> : null}
      </Descriptions>

      <Typography.Title level={4}>Consumo de insumos</Typography.Title>
      <Table
        rowKey="id"
        columns={lineColumns}
        dataSource={run.linhas}
        pagination={false}
        size="small"
      />
    </div>
  );
}
