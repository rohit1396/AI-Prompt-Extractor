import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

// https://vite.dev/config/
export default defineConfig({
  envDir: rootDir,
  plugins: [react(), tailwindcss()],
})
