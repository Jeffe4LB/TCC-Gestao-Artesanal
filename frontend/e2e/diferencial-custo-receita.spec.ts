import { test, expect } from "@playwright/test";
import { fazerLogin, temCredenciaisE2E } from "./helpers";

test.describe("Diferencial: custo por receita", () => {
  test.skip(!temCredenciaisE2E(), "Defina E2E_USERNAME e E2E_PASSWORD (backend em execução).");

  test("tela de receitas exibe prévia de custo", async ({ page }) => {
    await fazerLogin(page);
    await page.goto("/app/estoque/receitas");
    await expect(page.getByRole("heading", { name: /receitas/i })).toBeVisible();
    await expect(page.getByText(/custo estimado/i).first()).toBeVisible();
  });
});
