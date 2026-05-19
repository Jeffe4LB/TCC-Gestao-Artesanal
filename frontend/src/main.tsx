import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AntdAppProvider } from "./providers/AntdAppProvider";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AntdAppProvider>
      <App />
    </AntdAppProvider>
  </React.StrictMode>,
);
