/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Forbid en dash (U+2013) and em dash (U+2014) in source text.
 * Aligns with repo CI: .github/workflows/source-lint.yaml (check-forbidden-strings).
 * Use ASCII hyphen-minus (-) or rephrase (e.g. semicolon, comma).
 */

/** @type {import('eslint').Rule.RuleModule} */
export default {
  meta: {
    type: "problem",
    docs: {
      description:
        "disallow en dash (U+2013) and em dash (U+2014); use ASCII hyphen (-) instead",
    },
    messages: {
      forbidden:
        "Forbidden {{name}} ({{code}}). Use ASCII hyphen (-) or rephrase; see repo source-lint forbidden-strings check.",
    },
    schema: [],
  },
  create(context) {
    const forbidden = [
      ["\u2013", "en dash", "U+2013"],
      ["\u2014", "em dash", "U+2014"],
    ]

    return {
      Program(node) {
        const sourceCode = context.sourceCode
        // Full file text (includes comments); getText(node) omits comments.
        const lines = sourceCode.text.split("\n")

        for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
          const line = lines[lineIndex]

          for (const [character, name, code] of forbidden) {
            let column = line.indexOf(character)

            while (column !== -1) {
              context.report({
                node,
                loc: {
                  start: { line: lineIndex + 1, column },
                  end: { line: lineIndex + 1, column: column + 1 },
                },
                messageId: "forbidden",
                data: { name, code },
              })
              column = line.indexOf(character, column + 1)
            }
          }
        }
      },
    }
  },
}
