import { expect, type Page } from "@playwright/test";

export const credenciaisE2E = {
  username: process.env.E2E_USERNAME ?? "",
  password: process.env.E2E_PASSWORD ?? "",
};

export function temCredenciaisE2E(): boolean {
  return Boolean(credenciaisE2E.username && credenciaisE2E.password);
}

export async function fazerLogin(page: Page): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Usuário").fill(credenciaisE2E.username);
  await page.getByLabel("Senha").fill(credenciaisE2E.password);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).not.toHaveURL(/\/login$/);
}
