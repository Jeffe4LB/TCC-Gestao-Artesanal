import { apiPost } from "./clienteHttp";

export function trocarSenhaInicial(body: {
  new_password: string;
  new_password_confirm: string;
}): Promise<{ detail: string }> {
  return apiPost<{ detail: string }>("/auth/trocar-senha-inicial/", body);
}
