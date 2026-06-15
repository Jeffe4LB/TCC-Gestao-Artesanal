import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAutenticacao } from "../hooks/useAutenticacao";

export function RotaProtegida() {
  const { user, loading } = useAutenticacao();
  const location = useLocation();

  if (loading) {
    return (
      <div className="loading-screen">
        <p>Carregando sessão…</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (
    user.senha_temporaria &&
    location.pathname !== "/app/troca-senha-obrigatoria"
  ) {
    return <Navigate to="/app/troca-senha-obrigatoria" replace />;
  }

  return <Outlet />;
}
