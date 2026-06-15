import { useEffect, useState } from "react";
import { contarVencidosFinanceiros } from "../api/financeiro";

/** Quantidade de títulos em atraso (pagar + receber) para o menu. */
export function useContagemFinanceiroVencido() {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    contarVencidosFinanceiros()
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
