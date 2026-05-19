import { useEffect, useState } from "react";
import { fetchFinanceOverdueCount } from "../api/finance";

/** Quantidade de títulos em atraso (pagar + receber) para o menu. */
export function useFinanceOverdueCount() {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchFinanceOverdueCount()
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
