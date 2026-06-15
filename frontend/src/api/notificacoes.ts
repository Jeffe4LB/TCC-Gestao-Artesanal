import type {
  LinhaNotificacaoUsuario,
  NivelNotificacao,
  NotificacoesPaginadas,
  ResumoNotificacoes,
} from "../types/notificacoes";
import { apiGet, apiPost } from "./clienteHttp";

export type {
  LinhaNotificacaoUsuario,
  NivelNotificacao,
  NotificacoesPaginadas,
  ResumoNotificacoes,
} from "../types/notificacoes";

export function buscarResumoNotificacoes(
  diasAFrente = 7,
  previaEstoque = 10,
  de?: string,
  ate?: string,
): Promise<ResumoNotificacoes> {
  const q = new URLSearchParams({
    days_ahead: String(diasAFrente),
    stock_preview: String(previaEstoque),
  });
  if (de) q.set("from", de);
  if (ate) q.set("to", ate);
  return apiGet<ResumoNotificacoes>(`/notificacoes/resumo/?${q}`);
}

export function listarNotificacoesUsuario(params: {
  page?: number;
  pageSize?: number;
  unread?: boolean;
}): Promise<NotificacoesPaginadas> {
  const q = new URLSearchParams();
  if (params.page != null) q.set("page", String(params.page));
  if (params.pageSize != null) q.set("page_size", String(params.pageSize));
  if (params.unread) q.set("unread", "1");
  const suffix = q.toString() ? `?${q}` : "";
  return apiGet<NotificacoesPaginadas>(`/notificacoes/${suffix}`);
}

export function criarNotificacaoUsuario(payload: {
  nivel: NivelNotificacao;
  titulo: string;
  mensagem?: string;
}): Promise<LinhaNotificacaoUsuario> {
  return apiPost<LinhaNotificacaoUsuario>("/notificacoes/", {
    nivel: payload.nivel,
    titulo: payload.titulo,
    mensagem: payload.mensagem ?? "",
  });
}

export function marcarNotificacaoLida(id: number): Promise<LinhaNotificacaoUsuario> {
  return apiPost<LinhaNotificacaoUsuario>(`/notificacoes/${id}/lida/`);
}

export function marcarTodasNotificacoesLidas(): Promise<{ detail: string }> {
  return apiPost<{ detail: string }>("/notificacoes/marcar-todas-lidas/");
}





