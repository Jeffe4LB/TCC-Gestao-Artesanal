import { Navigate } from "react-router-dom";
import { useAutenticacao } from "../hooks/useAutenticacao";
import type { CapacidadesUsuario } from "../types/autenticacao";

type ChaveCapacidade = keyof CapacidadesUsuario;

export function ExigirCapacidade({
  need,
  children,
}: {
  need: ChaveCapacidade;
  children: React.ReactNode;
}) {
  const { user } = useAutenticacao();
  if (!user?.capacidades?.[need]) {
    return <Navigate to="/app" replace />;
  }
  return <>{children}</>;
}
