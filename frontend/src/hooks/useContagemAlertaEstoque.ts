import { useEffect, useState } from "react";
import { contarAlertasEstoque } from "../api/estoque";

/** Contagem de itens em alerta de estoque (para o menu). */
export function useContagemAlertaEstoque() {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    contarAlertasEstoque()
      .then((n) => {
        if (!cancelled) setCount(n);
      })
      .catch(() => {
        if (!cancelled) setCount(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return count;
}
