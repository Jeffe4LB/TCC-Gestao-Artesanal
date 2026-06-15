import type { PapelUsuario } from "../types/autenticacao";
import { apiDelete, apiGet, apiPatch, apiPost } from "./clienteHttp";

export type LinhaUsuarioAdmin = {
  id: number;
  username: string;
  email: string;
  ativo: boolean;
  papel: PapelUsuario;
  colaborador_dados_mestres: boolean;
  colaborador_estoque_leitura: boolean;
  colaborador_estoque_movimentacoes: boolean;
  colaborador_receitas_producao: boolean;
  colaborador_financeiro: boolean;
  colaborador_relatorios: boolean;
  colaborador_painel: boolean;
};


export type PatchUsuarioAdmin = Partial<{
  email: string;
  ativo: boolean;
  papel: PapelUsuario;
  colaborador_dados_mestres: boolean;
  colaborador_estoque_leitura: boolean;
  colaborador_estoque_movimentacoes: boolean;
  colaborador_receitas_producao: boolean;
  colaborador_financeiro: boolean;
  colaborador_relatorios: boolean;
  colaborador_painel: boolean;
}>;


export function listarUsuariosAdmin(): Promise<LinhaUsuarioAdmin[]> {
  return apiGet<LinhaUsuarioAdmin[]>("/auth/users/");
}

export function atualizarUsuarioAdmin(
  id: number,
  body: PatchUsuarioAdmin,
): Promise<LinhaUsuarioAdmin> {
  return apiPatch<LinhaUsuarioAdmin>(`/auth/users/${id}/`, body);
}

export type CriarUsuarioAdminBody = {
  nome: string;
  email: string;
  papel: PapelUsuario;
  colaborador_dados_mestres?: boolean;
  colaborador_estoque_leitura?: boolean;
  colaborador_estoque_movimentacoes?: boolean;
  colaborador_receitas_producao?: boolean;
  colaborador_financeiro?: boolean;
  colaborador_relatorios?: boolean;
  colaborador_painel?: boolean;
};

export function criarUsuarioAdmin(body: CriarUsuarioAdminBody): Promise<LinhaUsuarioAdmin> {
  return apiPost<LinhaUsuarioAdmin>("/auth/users/", body);
}

export function excluirUsuarioAdmin(id: number): Promise<void> {
  return apiDelete(`/auth/users/${id}/`);
}

export function resetarSenhaUsuarioAdmin(
  id: number,
): Promise<{ detail: string; email_enviado: boolean }> {
  return apiPost<{ detail: string; email_enviado: boolean }>(
    `/auth/users/${id}/resetar-senha/`,
  );
}


