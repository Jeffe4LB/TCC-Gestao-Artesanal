import type {
  Categoria,
  Cliente,
  Fornecedor,
  PaginatedResponse,
  Produto,
} from "../types/cadastro";
import type { HistoricoParceiroResponse } from "../types/financeiro";
import { apiDelete, apiGet, apiPatch, apiPost } from "./clienteHttp";

export function getProximoPath(proximo: string | null): string | null {
  if (!proximo) return null;
  try {
    const u = new URL(proximo);
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
export async function listarTodosProdutos(
  filters: Record<string, string | number | boolean | undefined> = {},
): Promise<Produto[]> {
  const all: Produto[] = [];
  let path: string | null = `/produtos/${toQuery({ page: 1, ...filters })}`;
  while (path) {
    const data = await apiGet<PaginatedResponse<Produto>>(path);
    all.push(...data.resultados);
    path = getProximoPath(data.proximo);
  }
  return all;
}


export async function listarCategorias(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<Categoria>> {
  return apiGet<PaginatedResponse<Categoria>>(`/categorias/${toQuery(params)}`);
}

export async function listarFornecedores(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<Fornecedor>> {
  return apiGet<PaginatedResponse<Fornecedor>>(`/fornecedores/${toQuery(params)}`);
}

export async function listarClientes(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<Cliente>> {
  return apiGet<PaginatedResponse<Cliente>>(`/clientes/${toQuery(params)}`);
}

export async function listarProdutos(
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<PaginatedResponse<Produto>> {
  return apiGet<PaginatedResponse<Produto>>(`/produtos/${toQuery(params)}`);
}

export async function listarTodasCategorias(): Promise<Categoria[]> {
  const all: Categoria[] = [];
  let path: string | null = "/categorias/?page=1";
  while (path) {
    const data = await apiGet<PaginatedResponse<Categoria>>(path);
    all.push(...data.resultados);
    path = getProximoPath(data.proximo);
  }
  return all;
}

export async function listarTodosFornecedores(): Promise<Fornecedor[]> {
  const all: Fornecedor[] = [];
  let path: string | null = "/fornecedores/?page=1&ativo=true";
  while (path) {
    const data = await apiGet<PaginatedResponse<Fornecedor>>(path);
    all.push(...data.resultados);
    path = getProximoPath(data.proximo);
  }
  return all;
}

export async function listarTodosClientes(): Promise<Cliente[]> {
  const all: Cliente[] = [];
  let path: string | null = "/clientes/?page=1&ativo=true";
  while (path) {
    const data = await apiGet<PaginatedResponse<Cliente>>(path);
    all.push(...data.resultados);
    path = getProximoPath(data.proximo);
  }
  return all;
}

export async function criarCategoria(body: { nome: string }): Promise<Categoria> {
  return apiPost<Categoria>("/categorias/", body);
}

export async function atualizarCategoria(
  id: number,
  body: Partial<{ nome: string }>,
): Promise<Categoria> {
  return apiPatch<Categoria>(`/categorias/${id}/`, body);
}

export async function excluirCategoria(id: number): Promise<void> {
  return apiDelete(`/categorias/${id}/`);
}

export async function criarFornecedor(
  body: Partial<Fornecedor> & { nome: string },
): Promise<Fornecedor> {
  return apiPost<Fornecedor>("/fornecedores/", body);
}

export async function atualizarFornecedor(
  id: number,
  body: Partial<Fornecedor>,
): Promise<Fornecedor> {
  return apiPatch<Fornecedor>(`/fornecedores/${id}/`, body);
}

export async function excluirFornecedor(id: number): Promise<void> {
  return apiDelete(`/fornecedores/${id}/`);
}

export async function criarCliente(
  body: Partial<Cliente> & { nome: string },
): Promise<Cliente> {
  return apiPost<Cliente>("/clientes/", body);
}

export async function atualizarCliente(
  id: number,
  body: Partial<Cliente>,
): Promise<Cliente> {
  return apiPatch<Cliente>(`/clientes/${id}/`, body);
}

export async function excluirCliente(id: number): Promise<void> {
  return apiDelete(`/clientes/${id}/`);
}

export async function criarProduto(body: Record<string, unknown>): Promise<Produto> {
  return apiPost<Produto>("/produtos/", body);
}

export async function atualizarProduto(
  id: number,
  body: Record<string, unknown>,
): Promise<Produto> {
  return apiPatch<Produto>(`/produtos/${id}/`, body);
}

export async function excluirProduto(id: number): Promise<void> {
  return apiDelete(`/produtos/${id}/`);
}

export async function obterHistoricoCliente(
  id: number,
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<HistoricoParceiroResponse> {
  return apiGet<HistoricoParceiroResponse>(
    `/clientes/${id}/historico-financeiro${toQuery(params)}`,
  );
}

export async function obterHistoricoFornecedor(
  id: number,
  params: Record<string, string | number | boolean | undefined> = {},
): Promise<HistoricoParceiroResponse> {
  return apiGet<HistoricoParceiroResponse>(
    `/fornecedores/${id}/historico-financeiro${toQuery(params)}`,
  );
}
