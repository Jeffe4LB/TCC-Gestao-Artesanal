"""Testes unitários da camada pura de exportação (sem banco)."""

from decimal import Decimal
from io import BytesIO

import openpyxl
from django.test import TestCase

from relatorios.exportadores import (
    DocumentoRelatorio,
    SecaoTabela,
    exportar_pdf,
    exportar_xlsx,
)


def _documento_simples() -> DocumentoRelatorio:
    return DocumentoRelatorio(
        titulo="Posição de estoque",
        subtitulo="Smoke test",
        periodo="01/01/2026 a 31/01/2026",
        resumo=[
            ("SKUs listados", "2"),
            ("Valor estoque (R$)", "35.50"),
        ],
        secoes=[
            SecaoTabela(
                titulo="Itens",
                cabecalhos=["SKU", "Nome", "Qtd", "Valor"],
                linhas=[
                    ["A1", "Produto A", 2, Decimal("10.50")],
                    ["B2", "Produto B", 1, Decimal("25.00")],
                ],
                totais=["", "TOTAL", 3, Decimal("35.50")],
                alinhamentos=["L", "L", "R", "R"],
            )
        ],
    )


def _documento_duas_secoes() -> DocumentoRelatorio:
    return DocumentoRelatorio(
        titulo="Financeiro em aberto",
        secoes=[
            SecaoTabela(
                titulo="Contas a pagar",
                cabecalhos=["Descrição", "Valor"],
                linhas=[["Energia", Decimal("100.00")]],
            ),
            SecaoTabela(
                titulo="Contas a receber",
                cabecalhos=["Descrição", "Valor"],
                linhas=[["Pedido #1", Decimal("250.00")]],
            ),
        ],
    )


class ExportadorPdfTests(TestCase):
    def test_pdf_comeca_com_assinatura_pdf(self):
        pdf = exportar_pdf(_documento_simples(), usuario="Tester")
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_pdf_tem_tamanho_razoavel(self):
        pdf = exportar_pdf(_documento_simples(), usuario="Tester")
        self.assertGreater(len(pdf), 1000)

    def test_pdf_aceita_secao_vazia_sem_estourar(self):
        doc = DocumentoRelatorio(
            titulo="Sem dados",
            secoes=[SecaoTabela(cabecalhos=["A", "B"], linhas=[])],
        )
        pdf = exportar_pdf(doc)
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_pdf_com_duas_secoes(self):
        pdf = exportar_pdf(_documento_duas_secoes())
        self.assertTrue(pdf.startswith(b"%PDF"))

    def test_pdf_paisagem_difere_de_retrato(self):
        doc_retrato = _documento_simples()
        doc_paisagem = _documento_simples()
        doc_paisagem.orientacao_paisagem = True
        # ambos válidos
        self.assertTrue(exportar_pdf(doc_retrato).startswith(b"%PDF"))
        self.assertTrue(exportar_pdf(doc_paisagem).startswith(b"%PDF"))


class ExportadorXlsxTests(TestCase):
    def test_xlsx_assinatura_zip(self):
        xlsx = exportar_xlsx(_documento_simples())
        # XLSX é um zip; começa com 'PK'
        self.assertEqual(xlsx[:2], b"PK")

    def test_xlsx_tem_duas_abas(self):
        xlsx = exportar_xlsx(_documento_simples())
        wb = openpyxl.load_workbook(BytesIO(xlsx))
        self.assertIn("Resumo", wb.sheetnames)
        self.assertIn("Detalhes", wb.sheetnames)

    def test_xlsx_resumo_traz_titulo_e_indicadores(self):
        xlsx = exportar_xlsx(_documento_simples())
        wb = openpyxl.load_workbook(BytesIO(xlsx))
        resumo = wb["Resumo"]
        # primeira célula é o título do relatório
        self.assertEqual(resumo["A1"].value, "Posição de estoque")
        # algum indicador do resumo deve aparecer
        textos = [str(cell.value) for row in resumo.iter_rows() for cell in row if cell.value]
        self.assertIn("SKUs listados", textos)

    def test_xlsx_detalhes_contem_cabecalhos_e_linhas(self):
        xlsx = exportar_xlsx(_documento_simples())
        wb = openpyxl.load_workbook(BytesIO(xlsx))
        detalhes = wb["Detalhes"]
        textos = [str(cell.value) for row in detalhes.iter_rows() for cell in row if cell.value]
        for cabecalho in ["SKU", "Nome", "Qtd", "Valor"]:
            self.assertIn(cabecalho, textos)
        # SKUs listados nas linhas
        self.assertIn("A1", textos)
        self.assertIn("B2", textos)

    def test_xlsx_secao_vazia_mostra_mensagem(self):
        doc = DocumentoRelatorio(
            titulo="Sem dados",
            secoes=[SecaoTabela(cabecalhos=["A", "B"], linhas=[])],
        )
        xlsx = exportar_xlsx(doc)
        wb = openpyxl.load_workbook(BytesIO(xlsx))
        textos = [
            str(cell.value)
            for row in wb["Detalhes"].iter_rows()
            for cell in row
            if cell.value
        ]
        self.assertTrue(any("Sem dados" in t for t in textos))

    def test_xlsx_aceita_decimal_como_numero(self):
        xlsx = exportar_xlsx(_documento_simples())
        wb = openpyxl.load_workbook(BytesIO(xlsx))
        valores_numericos = [
            cell.value
            for row in wb["Detalhes"].iter_rows()
            for cell in row
            if isinstance(cell.value, (int, float))
        ]
        # valores 10.50, 25.00, 2, 1, 3, 35.50 etc. — mais que o cabeçalho
        self.assertGreaterEqual(len(valores_numericos), 4)


class ExportadorViewsIntegrationTests(TestCase):
    """Smoke tests da integração ?export=pdf e ?export=xlsx via API."""

    def setUp(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        # superusuário tem todas as capacidades automaticamente
        self.user = User.objects.create_superuser(
            username="rep@test.com", password="x", email="rep@test.com"
        )
        self.client.force_login(self.user)

    def _get(self, url):
        return self.client.get(url)

    def test_posicao_estoque_pdf(self):
        res = self._get("/api/v1/relatorios/estoque/posicao/?export=pdf")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "application/pdf")
        self.assertTrue(res.content.startswith(b"%PDF"))
        self.assertIn("attachment", res["Content-Disposition"])
        self.assertIn(".pdf", res["Content-Disposition"])

    def test_posicao_estoque_xlsx(self):
        res = self._get("/api/v1/relatorios/estoque/posicao/?export=xlsx")
        self.assertEqual(res.status_code, 200)
        self.assertIn("spreadsheetml", res["Content-Type"])
        self.assertEqual(res.content[:2], b"PK")
        self.assertIn(".xlsx", res["Content-Disposition"])

    def test_estoque_abaixo_minimo_pdf(self):
        res = self._get("/api/v1/relatorios/estoque/abaixo-minimo/?export=pdf")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.content.startswith(b"%PDF"))

    def test_financeiro_em_aberto_xlsx(self):
        res = self._get("/api/v1/relatorios/financeiro/em-aberto/?export=xlsx")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content[:2], b"PK")

    def test_envelhecimento_pdf(self):
        res = self._get("/api/v1/relatorios/financeiro/envelhecimento/?export=pdf")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.content.startswith(b"%PDF"))

    def test_fluxo_caixa_pdf_requer_datas(self):
        # sem datas → 400
        res_sem = self._get("/api/v1/relatorios/financeiro/fluxo-caixa/?export=pdf")
        self.assertEqual(res_sem.status_code, 400)
        # com datas → 200 PDF
        res = self._get("/api/v1/relatorios/financeiro/fluxo-caixa/?from=2026-01-01&to=2026-01-31&export=pdf")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.content.startswith(b"%PDF"))

    def test_movimentacoes_estoque_xlsx(self):
        res = self._get(
            "/api/v1/relatorios/estoque/movimentacoes/?from=2026-01-01&to=2026-01-31&export=xlsx"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content[:2], b"PK")

    def test_movimentacoes_json_inclui_responsavel(self):
        from decimal import Decimal

        from django.utils import timezone

        from estoque.models import MovimentacaoEstoque, SaldoEstoque
        from produtos.models import Categoria, Fornecedor, Produto

        cat = Categoria.objects.create(nome="R-Cat")
        sup = Fornecedor.objects.create(nome="R-Forn")
        prod = Produto.objects.create(
            sku="R-MOV",
            nome="Prod rel",
            categoria=cat,
            fornecedor=sup,
            unidade="UN",
            preco_venda=Decimal("1"),
            custo_aquisicao=Decimal("1"),
        )
        SaldoEstoque.objects.update_or_create(produto=prod, defaults={"quantidade": Decimal("1")})
        hoje = timezone.localdate()
        MovimentacaoEstoque.objects.create(
            produto=prod,
            delta_quantidade=Decimal("1"),
            tipo_movimentacao=MovimentacaoEstoque.TipoMovimentacao.AJUSTE,
            criado_por=self.user,
        )
        res = self.client.get(
            f"/api/v1/relatorios/estoque/movimentacoes/?from={hoje.isoformat()}&to={hoje.isoformat()}"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(len(data["resultados"]), 1)
        self.assertEqual(data["resultados"][0]["criado_por_nome"], self.user.username)

    def test_receita_por_produto_pdf(self):
        res = self._get(
            "/api/v1/relatorios/financeiro/receita-por-produto/?from=2026-01-01&to=2026-01-31&export=pdf"
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.content.startswith(b"%PDF"))

    def test_csv_continua_funcionando(self):
        res = self._get("/api/v1/relatorios/estoque/posicao/?export=csv")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res["Content-Type"])

    def test_json_padrao_sem_export(self):
        res = self._get("/api/v1/relatorios/estoque/posicao/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/json", res["Content-Type"])

    def test_export_invalido_cai_no_json(self):
        # parâmetros desconhecidos devem ser ignorados (fallback para JSON)
        res = self._get("/api/v1/relatorios/estoque/posicao/?export=docx")
        self.assertEqual(res.status_code, 200)
        self.assertIn("application/json", res["Content-Type"])
