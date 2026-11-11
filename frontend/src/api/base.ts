/**
 * Base da API.
 *
 * Em desenvolvimento, deixe `VITE_API_URL` vazio para usar o proxy do Vite
 * (`/api` → localhost:8000). Em produção (Railway), defina no build:
 *   VITE_API_URL=https://seu-backend.up.railway.app
 */
const raw = (import.meta.env.VITE_API_URL as string | undefined)?.trim() ?? "";

export const API_ORIGIN = raw.replace(/\/$/, "");

export const API_PREFIX = API_ORIGIN ? `${API_ORIGIN}/api/v1` : "/api/v1";

/** Monta URL absoluta ou relativa para um path da API. */
export function apiUrl(path: string): string {
  if (path.startsWith("http")) return path;
  if (path.startsWith("/api/")) {
    return API_ORIGIN ? `${API_ORIGIN}${path}` : path;
  }
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${API_PREFIX}${p}`;
}
