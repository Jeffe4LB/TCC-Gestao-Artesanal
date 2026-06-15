import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ExigirCapacidade } from "./components/ExigirCapacidade";
import { AppLayout } from "./components/layout/AppLayout";
import { PainelPage } from "./pages/PainelPage";
import { ProvedorAutenticacao } from "./hooks/useAutenticacao";
import { ToastProvider } from "./hooks/useToast";
import { CategoriasPage } from "./pages/CategoriasPage";
import { ClientesPage } from "./pages/ClientesPage";
import { InicioPage } from "./pages/InicioPage";
import { EsqueciSenhaPage } from "./pages/EsqueciSenhaPage";
import { EntradaPage } from "./pages/EntradaPage";
import { CadastroPage } from "./pages/CadastroPage";
import { RedefinirSenhaPage } from "./pages/RedefinirSenhaPage";
import { ProdutosPage } from "./pages/ProdutosPage";
import { PublicInicioPage } from "./pages/InicioPublicoPage";
import { FornecedoresPage } from "./pages/FornecedoresPage";
import { DetalheOrdemProducaoPage } from "./pages/estoque/DetalheOrdemProducaoPage";
import { OrdensProducaoPage } from "./pages/estoque/OrdensProducaoPage";
import { ReceitasPage } from "./pages/estoque/ReceitasPage";
import { AlertasEstoquePage } from "./pages/estoque/AlertasEstoquePage";
import { SaldosEstoquePage } from "./pages/estoque/SaldosEstoquePage";
import { EntradaCompraPage } from "./pages/estoque/EntradaCompraPage";
import { SaidasEstoquePage } from "./pages/estoque/SaidasEstoquePage";
import { MovimentacoesEstoquePage } from "./pages/estoque/MovimentacoesEstoquePage";
import { ContasPagarPage } from "./pages/financeiro/ContasPagarPage";
import { ContasReceberPage } from "./pages/financeiro/ContasReceberPage";
import { DocumentosFinanceirosPage } from "./pages/financeiro/DocumentosFinanceirosPage";
import { FluxoCaixaPage } from "./pages/financeiro/FluxoCaixaPage";
import { AlertasFinanceirosPage } from "./pages/financeiro/AlertasFinanceirosPage";
import { RelatorioEnvelhecimentoPage } from "./pages/relatorios/RelatorioEnvelhecimentoPage";
import { RelatorioFluxoCaixaPage } from "./pages/relatorios/RelatorioFluxoCaixaPage";
import { RelatorioContasAbertoPage } from "./pages/relatorios/RelatorioContasAbertoPage";
import { RelatorioReceitaPorProdutoPage } from "./pages/relatorios/RelatorioReceitaPorProdutoPage";
import { RelatoriosInicioPage } from "./pages/relatorios/RelatoriosInicioPage";
import { TrocaSenhaObrigatoriaPage } from "./pages/TrocaSenhaObrigatoriaPage";
import { UsuariosAdminPage } from "./pages/UsuariosAdminPage";
import { RelatorioEstoqueAbaixoMinimoPage } from "./pages/relatorios/RelatorioEstoqueAbaixoMinimoPage";
import { RelatorioMovimentacoesEstoquePage } from "./pages/relatorios/RelatorioMovimentacoesEstoquePage";
import { RelatorioPosicaoEstoquePage } from "./pages/relatorios/RelatorioPosicaoEstoquePage";
import { RotaProtegida } from "./rotas/RotaProtegida";
import "./index.css";

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <ProvedorAutenticacao>
        <Routes>
          <Route path="/" element={<PublicInicioPage />} />
          <Route path="/login" element={<EntradaPage />} />
          <Route path="/registro" element={<CadastroPage />} />
          <Route path="/recuperar-senha" element={<EsqueciSenhaPage />} />
          <Route path="/redefinir-senha" element={<RedefinirSenhaPage />} />
          <Route element={<RotaProtegida />}>
            <Route
              path="/app/troca-senha-obrigatoria"
              element={<TrocaSenhaObrigatoriaPage />}
            />
            <Route element={<AppLayout />}>
              <Route path="/app" element={<InicioPage />} />
              <Route
                path="/app/dashboard"
                element={
                  <ExigirCapacidade need="painel">
                    <PainelPage />
                  </ExigirCapacidade>
                }
              />
              <Route
                path="/app/admin/usuarios"
                element={
                  <ExigirCapacidade need="gerenciar_usuarios">
                    <UsuariosAdminPage />
                  </ExigirCapacidade>
                }
              />
              <Route path="/app/notificacoes" element={<Navigate to="/app/dashboard" replace />} />
              <Route path="/app/cadastros/categorias" element={<CategoriasPage />} />
              <Route path="/app/cadastros/fornecedores" element={<FornecedoresPage />} />
              <Route path="/app/cadastros/clientes" element={<ClientesPage />} />
              <Route path="/app/cadastros/produtos" element={<ProdutosPage />} />
              <Route path="/app/estoque/saldos" element={<SaldosEstoquePage />} />
              <Route path="/app/estoque/entradas-compra" element={<EntradaCompraPage />} />
              <Route path="/app/estoque/saidas" element={<SaidasEstoquePage />} />
              <Route path="/app/estoque/movimentos" element={<MovimentacoesEstoquePage />} />
              <Route path="/app/estoque/alertas" element={<AlertasEstoquePage />} />
              <Route path="/app/estoque/receitas" element={<ReceitasPage />} />
              <Route path="/app/estoque/producao" element={<OrdensProducaoPage />} />
              <Route path="/app/estoque/producao/:id" element={<DetalheOrdemProducaoPage />} />
              <Route path="/app/financeiro/pagar" element={<ContasPagarPage />} />
              <Route path="/app/financeiro/receber" element={<ContasReceberPage />} />
              <Route path="/app/financeiro/documentos" element={<DocumentosFinanceirosPage />} />
              <Route path="/app/financeiro/fluxo-caixa" element={<FluxoCaixaPage />} />
              <Route path="/app/financeiro/alertas" element={<AlertasFinanceirosPage />} />
              <Route path="/app/relatorios" element={<RelatoriosInicioPage />} />
              <Route path="/app/relatorios/estoque/posicao" element={<RelatorioPosicaoEstoquePage />} />
              <Route path="/app/relatorios/estoque/movimentos" element={<RelatorioMovimentacoesEstoquePage />} />
              <Route path="/app/relatorios/estoque/abaixo-minimo" element={<RelatorioEstoqueAbaixoMinimoPage />} />
              <Route path="/app/relatorios/financeiro/em-aberto" element={<RelatorioContasAbertoPage />} />
              <Route path="/app/relatorios/financeiro/fluxo" element={<RelatorioFluxoCaixaPage />} />
              <Route path="/app/relatorios/financeiro/envelhecimento" element={<RelatorioEnvelhecimentoPage />} />
              <Route
                path="/app/relatorios/financeiro/receita-produto"
                element={<RelatorioReceitaPorProdutoPage />}
              />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </ProvedorAutenticacao>
      </ToastProvider>
    </BrowserRouter>
  );
}
