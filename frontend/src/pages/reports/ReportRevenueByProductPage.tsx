import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  DatePicker,
  Select,
  Space,
  Spin,
  Table,
  Typography,
} from "antd";
import dayjs from "dayjs";
import { fetchAllCategories, fetchAllCustomers } from "../../api/catalog";
import {
  downloadRevenueByProductCsv,
  fetchRevenueByProductReport,
} from "../../api/reports";
import type { Category, Customer } from "../../types/catalog";
import type { RevenueByProductReport, RevenueByProductRow } from "../../types/reports";
import type { ColumnsType } from "antd/es/table";
import { formatQuantityDisplay } from "../../utils/quantityDisplay";
import { firstDayOfMonthLocal, todayLocal } from "./dateRange";

export function ReportRevenueByProductPage() {
  const [from, setFrom] = useState(firstDayOfMonthLocal);
  const [to, setTo] = useState(todayLocal);
  const [customerId, setCustomerId] = useState<number | undefined>(undefined);
  const [categoryId, setCategoryId] = useState<number | undefined>(undefined);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [data, setData] = useState<RevenueByProductReport | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    void Promise.all([fetchAllCustomers(), fetchAllCategories()])
      .then(([cust, cats]) => {
        setCustomers(cust);
        setCategories(cats);
      })
      .catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await fetchRevenueByProductReport({
        from,
        to,
        customer: customerId,
        category: categoryId,
      });
      setData(res);
    } catch (e) {
      setData(null);
      setErr(e instanceof Error ? e.message : "Erro ao gerar");
    } finally {
      setLoading(false);
    }
  }, [from, to, customerId, categoryId]);

  useEffect(() => {
    void load();
  }, [load]);

  const exportCsv = async () => {
    setExporting(true);
    setErr(null);
    try {
      await downloadRevenueByProductCsv({
        from,
        to,
        customer: customerId,
        category: categoryId,
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  };

  const columns: ColumnsType<RevenueByProductRow> = useMemo(
    () => [
      { title: "SKU", dataIndex: "sku", key: "sku", width: 110 },
      { title: "Produto", dataIndex: "name", key: "name" },
      {
        title: "Categoria",
        dataIndex: "category",
        key: "category",
        width: 140,
        render: (v: string) => v || "—",
      },
      {
        title: "Qtd vendida",
        dataIndex: "quantity",
        key: "quantity",
        align: "right",
        render: (v: string) => formatQuantityDisplay(v),
      },
      {
        title: "Faturamento (R$)",
        dataIndex: "sales_total",
        key: "sales_total",
        align: "right",
      },
      { title: "Custo (R$)", dataIndex: "cost_total", key: "cost_total", align: "right" },
      { title: "Margem (R$)", dataIndex: "profit", key: "profit", align: "right" },
      {
        title: "Margem %",
        dataIndex: "margin_percent",
        key: "margin_percent",
        align: "right",
        render: (v: string) => `${v}%`,
      },
    ],
    [],
  );

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Typography.Title level={3} style={{ margin: 0 }}>
        Receita por produto
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Agregação das linhas de contas a receber pela data de emissão. Faturamento = soma dos totais
        das linhas; custo = quantidade × custo unitário atual do cadastro; margem = faturamento −
        custo.
      </Typography.Paragraph>

      <Card size="small" title="Filtros">
        <Space wrap>
          <DatePicker
            format="YYYY-MM-DD"
            value={dayjs(from)}
            onChange={(_, s) => setFrom(typeof s === "string" && s ? s : firstDayOfMonthLocal())}
          />
          <DatePicker
            format="YYYY-MM-DD"
            value={dayjs(to)}
            onChange={(_, s) => setTo(typeof s === "string" && s ? s : todayLocal())}
          />
          <Select
            placeholder="Cliente"
            allowClear
            style={{ width: 240 }}
            value={customerId}
            onChange={(v) => setCustomerId(v)}
            options={customers.map((c) => ({ value: c.id, label: c.name }))}
          />
          <Select
            placeholder="Categoria"
            allowClear
            style={{ width: 200 }}
            value={categoryId}
            onChange={(v) => setCategoryId(v)}
            options={categories.map((c) => ({ value: c.id, label: c.name }))}
          />
        </Space>
      </Card>

      <Space wrap>
        <Button onClick={() => void load()} loading={loading}>
          Atualizar
        </Button>
        <Button type="primary" onClick={() => void exportCsv()} loading={exporting}>
          Exportar CSV
        </Button>
      </Space>

      {err ? <Alert type="error" message={err} showIcon /> : null}

      <Spin spinning={loading && !data}>
        {data ? (
          <>
            <Typography.Text type="secondary">
              Período: {data.from} a {data.to} — {data.count} produto(s) com movimento.
            </Typography.Text>
            <Table<RevenueByProductRow>
              rowKey="product_id"
              columns={columns}
              dataSource={data.results}
              pagination={false}
              size="small"
              scroll={{ x: "max-content" }}
            />
          </>
        ) : null}
      </Spin>
    </Space>
  );
}
