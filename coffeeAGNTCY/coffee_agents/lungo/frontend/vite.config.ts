/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import { defineConfig } from "vitest/config"
import react from "@vitejs/plugin-react"
import path from "path"

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    fs: {
      strict: true,
      allow: [path.resolve(import.meta.dirname)],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "src"),
    },
    extensions: [".tsx", ".ts", ".jsx", ".js", ".json"],
  },
  build: {
    rolldownOptions: {
      treeshake: {
        // rolldown cannot tell that @open-ui-kit/core's unused namespace
        // Object.freeze({__proto__:null, ...}) statements are pure, so it keeps
        // the whole Graphics set (about +1.7 MB in the main chunk). Remove once
        // fixed upstream, and re-check the bundle size when bumping the library.
        manualPureFunctions: ["Object.freeze"],
      },
    },
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["src/test/setup.ts"],
  },
})
