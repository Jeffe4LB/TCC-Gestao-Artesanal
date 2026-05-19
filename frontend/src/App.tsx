import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { RequireCapability } from "./components/RequireCapability";
import { AppLayout } from "./components/layout/AppLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { AuthProvider } from "./hooks/useAuth";
import { ToastProvider } from "./hooks/useToast";
import { CategoriesPage } from "./pages/CategoriesPage";
import { CustomersPage } from "./pages/CustomersPage";
import { HomePage } from "./pages/HomePage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ResetPasswordPage } from "./pages/ResetPasswordPage";
import { ProductsPage } from "./pages/ProductsPage";
import { PublicHomePage } from "./pages/PublicHomePage";
import { SuppliersPage } from "./pages/SuppliersPage";
import { ProductionRunDetailPage } from "./pages/stock/ProductionRunDetailPage";
import { ProductionRunsPage } from "./pages/stock/ProductionRunsPage";
import { RecipesPage } from "./pages/stock/RecipesPage";
import { StockAlertsPage } from "./pages/stock/StockAlertsPage";
import { StockBalancesPage } from "./pages/stock/StockBalancesPage";
import { StockMovementsPage } from "./pages/stock/StockMovementsPage";
import { AccountsPayablePage } from "./pages/finance/AccountsPayablePage";
import { AccountsReceivablePage } from "./pages/finance/AccountsReceivablePage";
import { CashFlowPage } from "./pages/finance/CashFlowPage";
import { FinanceAlertsPage } from "./pages/finance/FinanceAlertsPage";
import { ReportFinanceAgingPage } from "./pages/reports/ReportFinanceAgingPage";
import { ReportFinanceCashFlowReportPage } from "./pages/reports/ReportFinanceCashFlowReportPage";
import { ReportFinanceOpenPage } from "./pages/reports/ReportFinanceOpenPage";
import { ReportRevenueByProductPage } from "./pages/reports/ReportRevenueByProductPage";
import { ReportsHomePage } from "./pages/reports/ReportsHomePage";
import { UsersAdminPage } from "./pages/UsersAdminPage";
import { ReportStockLowPage } from "./pages/reports/ReportStockLowPage";
import { ReportStockMovementsPage } from "./pages/reports/ReportStockMovementsPage";
import { ReportStockPositionPage } from "./pages/reports/ReportStockPositionPage";
import { ProtectedRoute } from "./routes/ProtectedRoute";
import "./index.css";

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
        <Routes>
          <Route path="/" element={<PublicHomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/registro" element={<RegisterPage />} />
          <Route path="/recuperar-senha" element={<ForgotPasswordPage />} />
          <Route path="/redefinir-senha" element={<ResetPasswordPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/app" element={<HomePage />} />
              <Route
                path="/app/dashboard"
                element={
                  <RequireCapability need="dashboard">
                    <DashboardPage />
                  </RequireCapability>
                }
              />
              <Route
                path="/app/admin/usuarios"
                element={
                  <RequireCapability need="manage_users">
                    <UsersAdminPage />
                  </RequireCapability>
                }
              />
              <Route path="/app/notificacoes" element={<Navigate to="/app/dashboard" replace />} />
              <Route path="/app/cadastros/categorias" element={<CategoriesPage />} />
              <Route path="/app/cadastros/fornecedores" element={<SuppliersPage />} />
              <Route path="/app/cadastros/clientes" element={<CustomersPage />} />
              <Route path="/app/cadastros/produtos" element={<ProductsPage />} />
              <Route path="/app/estoque/saldos" element={<StockBalancesPage />} />
              <Route path="/app/estoque/movimentos" element={<StockMovementsPage />} />
              <Route path="/app/estoque/alertas" element={<StockAlertsPage />} />
              <Route path="/app/estoque/receitas" element={<RecipesPage />} />
              <Route path="/app/estoque/producao" element={<ProductionRunsPage />} />
              <Route path="/app/estoque/producao/:id" element={<ProductionRunDetailPage />} />
              <Route path="/app/financeiro/pagar" element={<AccountsPayablePage />} />
              <Route path="/app/financeiro/receber" element={<AccountsReceivablePage />} />
              <Route path="/app/financeiro/fluxo-caixa" element={<CashFlowPage />} />
              <Route path="/app/financeiro/alertas" element={<FinanceAlertsPage />} />
              <Route path="/app/relatorios" element={<ReportsHomePage />} />
              <Route path="/app/relatorios/estoque/posicao" element={<ReportStockPositionPage />} />
              <Route path="/app/relatorios/estoque/movimentos" element={<ReportStockMovementsPage />} />
              <Route path="/app/relatorios/estoque/abaixo-minimo" element={<ReportStockLowPage />} />
              <Route path="/app/relatorios/financeiro/em-aberto" element={<ReportFinanceOpenPage />} />
              <Route path="/app/relatorios/financeiro/fluxo" element={<ReportFinanceCashFlowReportPage />} />
              <Route path="/app/relatorios/financeiro/envelhecimento" element={<ReportFinanceAgingPage />} />
              <Route
                path="/app/relatorios/financeiro/receita-produto"
                element={<ReportRevenueByProductPage />}
              />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
