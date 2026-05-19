import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Garante IPv4 (127.0.0.1) e a rede local: o default "localhost" pode escutar só em ::1,
    // e links no e-mail com http://127.0.0.1:5173 falham com ERR_CONNECTION_REFUSED.
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  // Sem isto, `npm run build` + `vite preview` envia /api para o próprio preview e o registo não grava no Django.
  preview: {
    host: true,
    port: 4173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
