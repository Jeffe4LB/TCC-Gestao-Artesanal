import { apiPost } from "./clienteHttp";

export type RegisterResponse = {
  id: number;
  username: string;
  email: string;
  /** Só em DEBUG no Django — confirme o mesmo ficheiro/host no cliente SQL. */
  _debug_database?: string;
};

export async function registerUser(body: {
  username: string;
  password: string;
  email?: string;
}): Promise<RegisterResponse> {
  return apiPost<RegisterResponse>("/auth/register/", {
    username: body.username,
    password: body.password,
    email: body.email?.trim() ?? "",
  });
}

export async function requestPasswordReset(
  email: string,
): Promise<{ detail: string; dev_notice?: string }> {
  return apiPost<{ detail: string; dev_notice?: string }>("/auth/password/forgot/", { email });
}

export async function confirmPasswordReset(body: {
  uid: string;
  token: string;
  new_password: string;
  new_password_confirm: string;
}): Promise<{ detail: string }> {
  return apiPost<{ detail: string }>(
    "/auth/password/reset/confirm/",
    body,
  );
}
