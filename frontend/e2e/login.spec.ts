import { test, expect } from "@playwright/test";

test("página de login exibe formulário", async ({ page }) => {
  await page.goto("/login");
  await expect(page.locator(".auth-card").getByText("Entrar", { exact: true }).first()).toBeVisible();
  await expect(page.getByLabel("Usuário")).toBeVisible();
  await expect(page.getByLabel("Senha")).toBeVisible();
  await expect(page.getByRole("button", { name: "Entrar" })).toBeEnabled();
});
