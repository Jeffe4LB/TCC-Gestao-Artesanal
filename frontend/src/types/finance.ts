import type { ProductUnitCode } from "../constants/units";

export type PayableStatus = "open" | "paid" | "cancelled";
export type ReceivableStatus = "open" | "paid" | "cancelled";

export type AccountReceivableLine = {
  id?: number;
  product: number | null;
  product_sku?: string | null;
  quantity: string;
  unit: ProductUnitCode;
  unit_price: string;
  discount: string;
  line_total: string;
};

export type AccountPayable = {
  id: number;
  supplier: number | null;
  supplier_name: string | null;
  description: string;
  amount: string;
  due_date: string;
  status: PayableStatus;
  paid_at: string | null;
  notes: string;
  created_by: number | null;
  created_at: string;
  updated_at: string;
};

export type AccountReceivable = {
  id: number;
  customer: number | null;
  customer_name: string | null;
  description: string;
  issue_date: string;
  amount: string;
  due_date: string;
  status: ReceivableStatus;
  received_at: string | null;
  notes: string;
  lines?: AccountReceivableLine[];
  created_by: number | null;
  created_at: string;
  updated_at: string;
};

export type CashFlowResponse = {
  from: string;
  to: string;
  inflows: string;
  outflows: string;
  net: string;
};

export type PayableAlertRow = {
  id: number;
  description: string;
  amount: string;
  due_date: string;
  supplier_name: string | null;
};

export type ReceivableAlertRow = {
  id: number;
  description: string;
  amount: string;
  due_date: string;
  customer_name: string | null;
};

export type FinanceAlertsResponse = {
  today: string;
  days_ahead: number;
  until: string;
  overdue: {
    payables: PayableAlertRow[];
    receivables: ReceivableAlertRow[];
  };
  due_soon: {
    payables: PayableAlertRow[];
    receivables: ReceivableAlertRow[];
  };
};
