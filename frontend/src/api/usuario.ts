import type { UsuarioSessao } from "../types/autenticacao";
import { apiGet } from "./clienteHttp";

export function buscarSessao(): Promise<UsuarioSessao> {
  return apiGet<UsuarioSessao>("/auth/me/");
}

