import { test, expect } from "@playwright/test";
import { fazerLogin, temCredenciaisE2E } from "./helpers";

test.describe("Diferencial: estoque ↔ financeiro", () => {
  test.skip(!temCredenciaisE2E(), "Defina E2E_USERNAME e E2E_PASSWORD (backend em execução).");

  test("navega de saldos para contas a receber após login", async ({ page }) => {
    await fazerLogin(page);
    await page.goto("/app/estoque/saldos");
    await expect(page.getByRole("heading", { name: /saldos/i })).toBeVisible();

    await page.goto("/app/financeiro/receber");
    await expect(page.getByRole("heading", { name: /contas a receber/i })).toBeVisible();
    await expect(page.getByText("Novo lançamento")).toBeVisible();
  });
});
