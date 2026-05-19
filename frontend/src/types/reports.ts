export type StockPositionRow = {
  sku: string;
  name: string;
  category: string;
  quantity: string;
  min_stock: string;
  below_minimum: boolean;
};

export type StockPositionReport = {
  count: number;
  results: StockPositionRow[];
};

export type StockMovementReportRow = {
  id: number;
  created_at: string;
  sku: string;
  product_name: string;
  quantity_delta: string;
  movement_type: string;
  notes: string;
};

export type StockMovementsReport = {
  from: string;
  to: string;
  count: number;
  results: StockMovementReportRow[];
};

export type StockLowRow = {
  sku: string;
  name: string;
  min_stock: string;
  current_quantity: string;
  gap: string;
};

export type StockLowReport = {
  count: number;
  results: StockLowRow[];
};

export type FinanceOpenPayableRow = {
  id: number;
  description: string;
  amount: string;
  due_date: string;
  supplier: string | null;
};

export type FinanceOpenReceivableRow = {
  id: number;
  description: string;
  amount: string;
  due_date: string;
  customer: string | null;
};

export type FinanceOpenReport = {
  summary: {
    payables_count: number;
    payables_total: string;
    receivables_count: number;
    receivables_total: string;
    net_open: string;
  };
  payables: FinanceOpenPayableRow[];
  receivables: FinanceOpenReceivableRow[];
};

export type FinanceCashFlowReport = {
  from: string;
  to: string;
  inflows: string;
  outflows: string;
  net: string;
};

export type AgingBucket = {
  count: number;
  total: string;
};

export type FinanceAgingReport = {
  today: string;
  payables: Record<string, AgingBucket>;
  receivables: Record<string, AgingBucket>;
};

export type RevenueByProductRow = {
  product_id: number;
  sku: string;
  name: string;
  category: string;
  quantity: string;
  sales_total: string;
  cost_total: string;
  profit: string;
  margin_percent: string;
};

export type RevenueByProductReport = {
  from: string;
  to: string;
  count: number;
  results: RevenueByProductRow[];
};
