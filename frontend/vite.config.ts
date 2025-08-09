import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
    // base: '/static/',
    build: {
        outDir: 'dist',
        assetsDir: 'assets'
    },
    // server: {
    //     // watch: null,

    //     proxy: {
    //         '/api': {
    //             target: "https://shqiw-talentmatch-backend.hf.space/",
    //             changeOrigin: true,
    //             // 'pathRewrite' is not supported in Vite proxy options; remove it or use a custom middleware if needed.
    //         },
    //         '/static': {
    //             target: "https://shqiw-talentmatch-backend.hf.space/",
    //             changeOrigin: true,
    //             // 'pathRewrite' is not supported in Vite proxy options; remove it or use a custom middleware if needed.
    //         }

    //     }
    // }
})
