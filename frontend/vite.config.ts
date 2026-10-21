import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The Django API runs on :8000. Proxying keeps everything same-origin in development,
// so there's no CORS setup to get wrong. Port 3000 matches FRONTEND_URL in Django settings.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/media": "http://127.0.0.1:8000",
    },
  },
});
