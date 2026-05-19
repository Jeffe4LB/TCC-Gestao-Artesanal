import type { ProductUnitCode } from "../constants/units";

export type { ProductUnitCode };

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Category = {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
};

export type Supplier = {
  id: number;
  name: string;
  legal_name: string;
  document: string;
  phone: string;
  email: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type Customer = {
  id: number;
  name: string;
  document: string;
  phone: string;
  email: string;
  address: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ProductType = "purchased" | "manufactured";

export type ProductCostOrigin = "purchase" | "bom";

export type Product = {
  id: number;
  sku: string;
  name: string;
  description: string;
  category: number;
  category_name: string;
  supplier: number | null;
  supplier_name: string | null;
  product_type: ProductType;
  unit: ProductUnitCode;
  sale_price: string;
  purchase_unit_cost: string;
  unit_cost: string;
  cost_origin: ProductCostOrigin;
  min_stock: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};
