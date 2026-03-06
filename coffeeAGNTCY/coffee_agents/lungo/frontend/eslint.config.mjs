import js from "@eslint/js"
import globals from "globals"
import reactHooks from "eslint-plugin-react-hooks"
import reactRefresh from "eslint-plugin-react-refresh"
import tseslint from "typescript-eslint"
import tsparser from "@typescript-eslint/parser"
import tsplugin from "@typescript-eslint/eslint-plugin"
import prettier from "eslint-plugin-prettier"
import prettierConfig from "eslint-config-prettier"

export default [
  { ignores: ["dist", "node_modules"] },
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      globals: {
        ...globals.browser,
        React: "readonly",
      },
      parser: tsparser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
        sourceType: "module",
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
      "@typescript-eslint": tsplugin,
      prettier: prettier,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      ...prettierConfig.rules,
      "prettier/prettier": "error",

      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],
      "no-useless-catch": "off",
      "no-dupe-keys": "error",
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": [
        "error",
      ],
      "max-lines": ["warn", { max: 400 }],
    },
  },
  {
    files: ["vite.config.ts", "**/*.config.js", "**/logger.ts"],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      "@typescript-eslint/no-require-imports": "off",
      "no-console": "off",
    },
  },
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    ignores: ["**/logger.ts"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']",
          message:
            "dangerouslySetInnerHTML can lead to XSS. Render user or API content as text only (e.g. {value}).",
        },
        {
          selector: "MemberExpression[property.name='innerHTML']",
          message:
            "innerHTML can lead to XSS. Render user or API content as text only (e.g. textContent or React text children).",
        },
        {
          selector: "MemberExpression[object.name='unsafeLogger']",
          message:
            "unsafeLogger may expose data in production. Use only for non-sensitive diagnostics; do not log PII, full responses, or raw payloads. Consider adding // unsafe-logger: <reason>.",
        },
      ],
    },
  },
  {
    files: ["**/useApp.ts", "**/useMainArea.ts", "**/graphConfigsData.tsx"],
    rules: {
      "max-lines": "off",
    },
  },
]
