import { test, expect, type Page } from "@playwright/test";
import { fazerLogin, temCredenciaisE2E } from "./helpers";

async function registrarProducaoMinima(page: Page): Promise<void> {
  const card = page.locator(".ant-card").filter({ hasText: "Nova ordem de produção" });

  await card
    .locator(".ant-form-item")
    .filter({ hasText: "Produto fabricado" })
    .locator(".ant-select")
    .click();
  await page.locator(".ant-select-item-option").first().click();

  await card.getByPlaceholder("> 0").fill("1");

  const linhaInsumo = card.locator(".ant-form-item").filter({ hasText: /^Insumo$/ }).first();
  const insumoSelect = linhaInsumo.locator(".ant-select");
  const insumoPreenchido = await insumoSelect.locator(".ant-select-selection-item").count();
  if (insumoPreenchido === 0) {
    await insumoSelect.click();
    await page.locator(".ant-select-item-option").first().click();
    await card
      .locator(".ant-form-item")
      .filter({ hasText: "Qtd consumida" })
      .first()
      .getByRole("textbox")
      .fill("1");
  }

  const submit = card.getByRole("button", { name: "Registrar produção" });
  await Promise.all([
    page.waitForResponse(
      (r) =>
        r.url().includes("/ordens-producao/") &&
        r.request().method() === "POST" &&
        r.status() === 201,
    ),
    submit.click(),
  ]);

  await expect(page.getByText("Ativa").first()).toBeVisible({ timeout: 15_000 });
}

async function confirmarCancelamentoProducao(page: Page): Promise<void> {
  await page.getByLabel("Cancelar produção").first().click();
  await page
    .locator(".ant-popconfirm")
    .getByRole("button", { name: "Cancelar produção" })
    .click();
}

test.describe("Diferencial: produção", () => {
  test.skip(!temCredenciaisE2E(), "Defina E2E_USERNAME e E2E_PASSWORD (backend em execução).");

  test("tela de produção exibe formulário de nova ordem", async ({ page }) => {
    await fazerLogin(page);
    await page.goto("/app/estoque/producao");
    await expect(page.getByRole("heading", { name: "Produção" })).toBeVisible();
    await expect(page.getByText("Nova ordem de produção")).toBeVisible();
    await expect(page.getByRole("button", { name: "Registrar produção" })).toBeVisible();
  });

  test("cancelar produção exibe situação cancelada na lista", async ({ page }) => {
    await fazerLogin(page);
    await page.goto("/app/estoque/producao");
    await registrarProducaoMinima(page);
    await confirmarCancelamentoProducao(page);
    await expect(page.getByText("Cancelada").first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByLabel("Cancelar produção")).toHaveCount(0);
  });

  test("detalhe de produção cancelada não exibe botão cancelar", async ({ page }) => {
    await fazerLogin(page);
    await page.goto("/app/estoque/producao");
    await registrarProducaoMinima(page);
    await confirmarCancelamentoProducao(page);
    await page.getByRole("link", { name: "Ver" }).first().click();
    await expect(page.getByRole("button", { name: "Cancelar produção" })).toHaveCount(0);
    await expect(page.getByText(/Produção cancelada em/i)).toBeVisible();
  });
});
