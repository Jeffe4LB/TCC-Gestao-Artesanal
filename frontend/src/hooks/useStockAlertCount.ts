import { useEffect, useState } from "react";
import { fetchStockAlertCount } from "../api/stock";

/** Contagem de itens em alerta de estoque (para o menu). */
export function useStockAlertCount() {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchStockAlertCount()
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
