import { App, ConfigProvider, theme } from "antd";
import ptBR from "antd/locale/pt_BR";
import type { ReactNode } from "react";

export function AntdAppProvider({ children }: { children: ReactNode }) {
  return (
    <ConfigProvider
      locale={ptBR}
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: "#007681",
          borderRadius: 6,
        },
      }}
    >
      <App>{children}</App>
    </ConfigProvider>
  );
}
