import { clearTokens, getAccessToken, tryRefreshToken } from "./sessao";

const API_PREFIX = "/api/v1";

function joinUrl(path: string): string {
  if (path.startsWith("http")) return path;
  if (path.startsWith("/api/v1")) return path;
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_PREFIX}${p}`;
}

/** Rotas que não devem enviar Bearer (token inválido geraria 401 antes do AllowAny). */
function isPublicAuthPath(path: string): boolean {
  const u = joinUrl(path);
  return (
    u.includes("/auth/password/") ||
    u.includes("/auth/register/") ||
    u.includes("/auth/token/")
  );
}

/** Rótulos em português para nomes de campo vindos da API (erros de validação). */
const ROTULO_CAMPO_API: Record<string, string> = {
  detail: "Detalhe",
  nome: "Nome",
  sku: "Código (SKU)",
  descricao: "Descrição",
  documento: "Documento",
  telefone: "Telefone",
  email: "E-mail",
  endereco: "Endereço",
  ativo: "Ativo",
  categoria: "Categoria",
  fornecedor: "Fornecedor",
  cliente: "Cliente",
  produto: "Produto",
  insumo: "Insumo",
  quantidade: "Quantidade",
  unidade: "Unidade",
  valor: "Valor",
  vencimento: "Vencimento",
  data_emissao: "Emissão",
  situacao: "Situação",
  pago_em: "Pago em",
  recebido_em: "Recebido em",
  observacoes: "Observações",
  linhas: "Linhas",
  tipo_movimentacao: "Tipo de movimentação",
  tipo_produto: "Tipo de produto",
  custo_aquisicao: "Custo de aquisição",
  preco_venda: "Preço de venda",
  estoque_minimo: "Estoque mínimo",
  username: "Usuário",
  password: "Senha",
  new_password: "Nova senha",
  new_password_confirm: "Confirmação da senha",
  role: "Perfil",
  quantidade_consumida_unidade: "Unidade consumida",
  quantidade_produzida_unidade: "Unidade produzida",
};

function rotuloCampoApi(chave: string): string {
  return ROTULO_CAMPO_API[chave] ?? chave.replace(/_/g, " ");
}

/** Formata valores de erro do DRF (listas, objetos aninhados, não-field). */
function formatDrfValue(v: unknown): string {
  if (v === null || v === undefined) return "";
  if (typeof v === "string") return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  if (Array.isArray(v)) return v.map((x) => formatDrfValue(x)).filter(Boolean).join(", ");
  if (typeof v === "object") {
    return Object.entries(v as Record<string, unknown>)
      .map(([k, val]) => `${rotuloCampoApi(k)}: ${formatDrfValue(val)}`)
      .join("; ");
  }
  return String(v);
}

function parseErrorBody(err: unknown): string {
  if (typeof err !== "object" || err === null) return "Erro na requisição";
  const o = err as Record<string, unknown>;
  if (typeof o.detail === "string") return o.detail;
  if (Array.isArray(o.detail)) return o.detail.map(String).join(" ");
  const parts: string[] = [];
  for (const [k, v] of Object.entries(o)) {
    if (k === "detail") continue;
    parts.push(`${rotuloCampoApi(k)}: ${formatDrfValue(v)}`);
  }
  if (parts.length) return parts.join("; ");
  return "Erro na requisição";
}

/** Útil em formulários quando se captura o corpo JSON manualmente. */
export function formatApiErrorPayload(err: unknown): string {
  return parseErrorBody(err);
}

/**
 * Fetch autenticado; em 401 tenta refresh uma vez e repete a requisição.
 */
export async function apiFetch(
  path: string,
  init: RequestInit = {},
  allowRetry = true,
): Promise<Response> {
  const headers = new Headers(init.headers);
  if (
    init.body &&
    !(init.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }
  const skipAuth = isPublicAuthPath(path);
  const token = skipAuth ? null : getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let res = await fetch(joinUrl(path), { ...init, headers });

  if (res.status === 401 && allowRetry && !skipAuth) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      const headers2 = new Headers(init.headers);
      if (
        init.body &&
        !(init.body instanceof FormData) &&
        !headers2.has("Content-Type")
      ) {
        headers2.set("Content-Type", "application/json");
      }
      const t2 = getAccessToken();
      if (t2) headers2.set("Authorization", `Bearer ${t2}`);
      res = await fetch(joinUrl(path), { ...init, headers: headers2 });
    } else {
      clearTokens();
    }
  }

  return res;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await apiFetch(path, { method: "GET" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401 && !isPublicAuthPath(path)) {
      throw new Error("Sessão expirada. Entre novamente.");
    }
    throw new Error(parseErrorBody(err));
  }
  return res.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await apiFetch(path, {
    method: "POST",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401 && !isPublicAuthPath(path)) {
      throw new Error("Sessão expirada. Entre novamente.");
    }
    throw new Error(parseErrorBody(err));
  }
  return res.json() as Promise<T>;
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await apiFetch(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401 && !isPublicAuthPath(path)) {
      throw new Error("Sessão expirada. Entre novamente.");
    }
    throw new Error(parseErrorBody(err));
  }
  return res.json() as Promise<T>;
}

export async function apiDelete(path: string): Promise<void> {
  const res = await apiFetch(path, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    const err = await res.json().catch(() => ({}));
    if (res.status === 401 && !isPublicAuthPath(path)) {
      throw new Error("Sessão expirada. Entre novamente.");
    }
    throw new Error(parseErrorBody(err));
  }
}
