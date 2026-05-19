export type StockBalanceRow = {
  id: number;
  product: number;
  product_sku: string;
  product_name: string;
  quantity: string;
  base_unit?: string;
};

export type StockMovementRow = {
  id: number;
  product: number;
  product_sku: string;
  quantity_delta: string;
  quantity_input?: string | null;
  unit_input?: string | null;
  base_unit?: string;
  movement_type: string;
  production_run: number | null;
  notes: string;
  created_by: number | null;
  created_at: string;
};

export type StockAlertRow = {
  product_id: number;
  sku: string;
  name: string;
  min_stock: string;
  current_quantity: string;
  gap: string;
};

export type RecipeLine = {
  id?: number;
  component: number;
  component_sku?: string;
  quantity_per_unit: string;
};

export type Recipe = {
  id: number;
  product: number;
  notes: string;
  lines: RecipeLine[];
  created_at: string;
  updated_at: string;
};

export type ProductionRunLine = {
  id: number;
  component: number;
  component_sku: string;
  component_name: string;
  quantity_consumed: string;
};

export type ProductionRun = {
  id: number;
  product: number;
  product_sku: string;
  product_name: string;
  quantity_produced: string;
  notes: string;
  lines: ProductionRunLine[];
  created_by: number | null;
  created_at: string;
};
