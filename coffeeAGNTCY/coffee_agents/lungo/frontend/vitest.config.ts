/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

import path from "path"
import { fileURLToPath } from "url"
import { defineConfig } from "vitest/config"
import react from "@vitejs/plugin-react"

const dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["src/test/setup.ts"],
  },
  resolve: {
    alias: {
      "@": path.resolve(dirname, "src"),
    },
    extensions: [".tsx", ".ts", ".jsx", ".js", ".json"],
  },
})
