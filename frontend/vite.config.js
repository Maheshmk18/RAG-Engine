import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  css: {
    transformer: 'postcss',
    minify: true
  },
  server: {
    host: "0.0.0.0",
    port: 5001,
    proxy: {
      "/api": {
        target: "http://localhost:8002",
        changeOrigin: true
      }
    }
  },
  preview: {
    host: "0.0.0.0",
    port: 5001
  }
});
