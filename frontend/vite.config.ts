import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],

    server: {
        // watch: null,

        proxy: {
            '/api': {
                target: "http://127.0.0.1:5000",
                changeOrigin: true,
                // 'pathRewrite' is not supported in Vite proxy options; remove it or use a custom middleware if needed.
            },

        }
    }
})
