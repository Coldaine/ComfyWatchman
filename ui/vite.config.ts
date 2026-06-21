/*
 * @Author: 晴知 qingli.hql@alibaba-inc.com
 * @Date: 2024-12-10 22:11:57
 * @LastEditors: ai-business-hql ai.bussiness.hql@gmail.com
 * @LastEditTime: 2025-02-25 20:58:44
 * @FilePath: /comfyui_copilot/ui/vite.config.ts
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { exec } from 'child_process';
import path from 'path';
import tailwindcss from 'tailwindcss';
import autoprefixer from 'autoprefixer';
import postcssNesting from 'postcss-nesting';

const rewriteImportPlugin = ({ isDev }) => {
  return {
    name: "rewrite-import-plugin", // this name will show up in warnings and errors
    resolveId(source) {
      if (!isDev) {
        return;
      }
      if (source === "/scripts/app.js") {
        // Change the path to the new host
        return "http://127.0.0.1:8188/scripts/app.js";
      }
      if (source === "/scripts/api.js") {
        return "http://127.0.0.1:8188/scripts/api.js";
      }
      return null; // Other imports should not be affected
    },
  };
};

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  envDir: ".",
  css: {
    postcss: {
      plugins: [
        postcssNesting(),
        tailwindcss(),
        autoprefixer(),
      ],
    },
  },
  build: {
    watch: mode === "development" ? {
      include: ["src/**"],
      buildStart() {
        // 只在开发模式下启动 Tailwind CSS watch 进程
        console.log("Starting Tailwind CSS watch process...");
        const tailwindProcess = exec(
          'npx tailwindcss -i ./src/scoped-tailwind.css -o ./src/output.css --watch',
          (error, stdout, stderr) => {
            if (error) {
              console.error(`Tailwind CSS watch error: ${error}`);
              return;
            }
            if (stderr) {
              console.error(`Tailwind CSS stderr: ${stderr}`);
              return;
            }
            console.log(`Tailwind CSS stdout: ${stdout}`);
          }
        );

        // Cleanup process on build end
        process.on('exit', () => {
          tailwindProcess.kill();
        });
        console.log("Tailwind CSS watch process started.");
      }
    } : undefined,  // 在生产环境下不启用 watch
    // minify: false, // ___DEBUG__MODE only
    // sourcemap: true, // ___DEBUG___MODE only
    emptyOutDir: true,
    rollupOptions: {
      // externalize deps that shouldn't be bundled into your library
      external: ["/scripts/app.js", "/scripts/api.js"],
      input: {
        input: "/src/main.tsx",
        fonts: "/src/fonts.css"
      },
      output: {
        // Provide global variables to use in the UMD build for externalized deps
        globals: {
          app: "app",
          Litegraph: "LiteGraph",
        },
        dir: "../dist",
        // assetFileNames: "[name]-[hash][extname]",
        entryFileNames: "copilot_web/[name].js",
        chunkFileNames: `copilot_web/[name]-[hash].js`,
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === 'fonts.css') {
            return 'copilot_web/[name].css';
          }
          return `copilot_web/assets/[name]-[hash].[ext]`;
        },
        manualChunks: {
          // 只包含实际使用的 React 相关依赖
          'vendor-react': ['react', 'react-dom'],
          
          // Markdown 相关依赖
          'vendor-markdown': [
            'react-markdown',
            'remark-gfm',
            'remark-math',
            'rehype-katex',
            'rehype-external-links'
          ],
          
          // UI 组件
          'vendor-ui': [
            '@heroicons/react'
          ],
          
          // 消息组件
          'message-components': [
            './src/components/chat/messages/AIMessage',
            './src/components/chat/messages/UserMessage',
            './src/components/chat/messages/NodeInstallGuide',
            './src/components/chat/messages/NodeSearch',
            './src/components/chat/messages/DownstreamSubgraphs',
          ],
        }
      },
    },
    // Enable compression
    target: 'esnext',
    minify: 'esbuild',
    cssMinify: true,
    chunkSizeWarningLimit: 600 // 适当调整警告阈值
  },
  plugins: [react(), rewriteImportPlugin({ isDev: mode === "development" })],
}));
