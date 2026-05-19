import type {
  Category,
  Customer,
  PaginatedResponse,
  Product,
  Supplier,
} from "../types/catalog";
import { apiDelete, apiGet, apiPatch, apiPost } from "./client";

export function getNextPath(next: string | null): string | null {
  if (!next) return null;
  try {
    const u = new URL(next);
    return u.pathname + u.search;
  } catch {
    return null;
  }
}

export function toQuery(
  params: Record<string, string | number | boolean | undefined>,
): string {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") q.set(k, String(v));
  });
  const s = q.toString();
  return s ? `?${s}` : "";
}

/** Todas as páginas de produtos (para selects). */
export async function fetchAllProducts(
  filters: Record<string, string | number | boolean | undefined> = {},
): Promise<Product[]> {
  const all: Product[] = [];
  let path: string | null = `/products/${toQuery({ page: 1, ...filters })}`;
  while (path) {
    const data = await apiGet<PaginatedResponse<Product>>(path);
    all.push(...data.results);
    path = getNextPath(data.next);
  }
  return all;
}

/** Lista paginada (page padrão 1, 20 itens no backend). */
export async function listCategories(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<Category>> {
  return apiGet<PaginatedResponse<Category>>(`/categories/${toQuery(params)}`);
}

export async function listSuppliers(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<Supplier>> {
  return apiGet<PaginatedResponse<Supplier>>(`/suppliers/${toQuery(params)}`);
}

export async function listCustomers(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<Customer>> {
  return apiGet<PaginatedResponse<Customer>>(`/customers/${toQuery(params)}`);
}

export async function listProducts(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<Product>> {
  return apiGet<PaginatedResponse<Product>>(`/products/${toQuery(params)}`);
}

export async function fetchAllCategories(): Promise<Category[]> {
  const all: Category[] = [];
  let path: string | null = "/categories/?page=1";
  while (path) {
    const data = await apiGet<PaginatedResponse<Category>>(path);
    all.push(...data.results);
    path = getNextPath(data.next);
  }
  return all;
}

export async function fetchAllSuppliers(): Promise<Supplier[]> {
  const all: Supplier[] = [];
  let path: string | null = "/suppliers/?page=1&is_active=true";
  while (path) {
    const data = await apiGet<PaginatedResponse<Supplier>>(path);
    all.push(...data.results);
    path = getNextPath(data.next);
  }
  return all;
}

export async function fetchAllCustomers(): Promise<Customer[]> {
  const all: Customer[] = [];
  let path: string | null = "/customers/?page=1&is_active=true";
  while (path) {
    const data = await apiGet<PaginatedResponse<Customer>>(path);
    all.push(...data.results);
    path = getNextPath(data.next);
  }
  return all;
}

export async function createCategory(body: { name: string }): Promise<Category> {
  return apiPost<Category>("/categories/", body);
}

export async function updateCategory(id: number, body: Partial<{ name: string }>): Promise<Category> {
  return apiPatch<Category>(`/categories/${id}/`, body);
}

export async function deleteCategory(id: number): Promise<void> {
  return apiDelete(`/categories/${id}/`);
}

export async function createSupplier(
  body: Partial<Supplier> & { name: string },
): Promise<Supplier> {
  return apiPost<Supplier>("/suppliers/", body);
}

export async function updateSupplier(
  id: number,
  body: Partial<Supplier>,
): Promise<Supplier> {
  return apiPatch<Supplier>(`/suppliers/${id}/`, body);
}

export async function deleteSupplier(id: number): Promise<void> {
  return apiDelete(`/suppliers/${id}/`);
}

export async function createCustomer(
  body: Partial<Customer> & { name: string },
): Promise<Customer> {
  return apiPost<Customer>("/customers/", body);
}

export async function updateCustomer(
  id: number,
  body: Partial<Customer>,
): Promise<Customer> {
  return apiPatch<Customer>(`/customers/${id}/`, body);
}

export async function deleteCustomer(id: number): Promise<void> {
  return apiDelete(`/customers/${id}/`);
}

export async function createProduct(
  body: Record<string, unknown>,
): Promise<Product> {
  return apiPost<Product>("/products/", body);
}

export async function updateProduct(
  id: number,
  body: Record<string, unknown>,
): Promise<Product> {
  return apiPatch<Product>(`/products/${id}/`, body);
}

export async function deleteProduct(id: number): Promise<void> {
  return apiDelete(`/products/${id}/`);
}
