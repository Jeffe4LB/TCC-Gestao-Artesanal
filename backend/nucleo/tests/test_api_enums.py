from django.test import SimpleTestCase

from estoque.models import MovimentacaoEstoque
from nucleo.api_enums import (
    tipo_movimentacao_do_api,
    tipo_movimentacao_para_api,
)


class TipoMovimentacaoApiEnumTests(SimpleTestCase):
    def test_entrada_producao_roundtrip(self):
        db = MovimentacaoEstoque.TipoMovimentacao.ENTRADA_PRODUCAO
        api = tipo_movimentacao_para_api(db)
        self.assertEqual(api, "entrada_producao")
        self.assertEqual(tipo_movimentacao_do_api(api), db)

    def test_legacy_saida_producao_alias(self):
        db = tipo_movimentacao_do_api("saida_producao")
        self.assertEqual(db, MovimentacaoEstoque.TipoMovimentacao.ENTRADA_PRODUCAO)

    def test_estorno_entrada_producao_roundtrip(self):
        db = MovimentacaoEstoque.TipoMovimentacao.ESTORNO_ENTRADA_PRODUCAO
        api = tipo_movimentacao_para_api(db)
        self.assertEqual(api, "estorno_entrada_producao")
        self.assertEqual(tipo_movimentacao_do_api(api), db)

    def test_estorno_consumo_producao_roundtrip(self):
        db = MovimentacaoEstoque.TipoMovimentacao.ESTORNO_CONSUMO_PRODUCAO
        api = tipo_movimentacao_para_api(db)
        self.assertEqual(api, "estorno_consumo_producao")
        self.assertEqual(tipo_movimentacao_do_api(api), db)
