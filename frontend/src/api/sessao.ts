import { AUTH_TOKENS_CLEARED_EVENT } from "../constants/eventosAutenticacao";

const API = "/api/v1";
const JSON_HEADERS = { "Content-Type": "application/json" };

export function getAccessToken(): string | null {
  return localStorage.getItem("access");
}

export function getRefreshToken(): string | null {
  return localStorage.getItem("refresh");
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem("access", access);
  localStorage.setItem("refresh", refresh);
}

export function setAccessToken(access: string): void {
  localStorage.setItem("access", access);
}

export function clearTokens(): void {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  if (typeof window !== "undefined") {
    window.dispatchEvent(new Event(AUTH_TOKENS_CLEARED_EVENT));
  }
}

export async function login(username: string, password: string): Promise<void> {
  const r = await fetch(`${API}/auth/token/`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ username, password }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(formatApiError(err));
  }
  const data = (await r.json()) as { access: string; refresh: string };
  setTokens(data.access, data.refresh);
}

/** Atualiza access via refresh (sem passar pelo client, evita ciclo). */
export async function tryRefreshToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  const r = await fetch(`${API}/auth/token/refresh/`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ refresh }),
  });
  if (!r.ok) {
    clearTokens();
    return false;
  }
  const data = (await r.json()) as { access: string };
  setAccessToken(data.access);
  return true;
}

function formatApiError(err: unknown): string {
  if (typeof err === "object" && err !== null && "detail" in err) {
    const d = (err as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return d.map((x) => String(x)).join(" ");
  }
  return "Erro na requisição";
}
