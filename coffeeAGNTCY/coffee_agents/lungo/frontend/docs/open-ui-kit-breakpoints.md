# New breakpoints

This document summarizes responsive and layout-related behavior of Open UI Kit.

**Single source of truth:** The **`theme.breakpoints.values`** contract for this product is defined in the table below. Other docs under `docs/` must match these numbers; link here instead of duplicating ad hoc values.

---

## Canonical `theme.breakpoints.values` (px, min-width)

| Key | Min width (px) | Notes |
| --- | ---: | --- |
| `xs` | `0` | MUI convention: base / default styles |
| `sm` | `600` | Compact vs wider layouts; below typical iPad portrait (~768px) |
| `md` | `1024` | First “comfortable product UI” / small laptop step |
| `lg` | `1440` | Large desktop frame |
| `xl` | `1920` | Extra-wide desktop |
| `xxl` | `2560` | Ultra-wide |

Ordered keys (ascending width): `xs`, `sm`, `md`, `lg`, `xl`, `xxl`.

---

## Breakpoint scale: intentional product choice (not Material defaults)

We keep a **product-specific** pixel ladder (`xs` → `xxl` in `theme/common.tsx`), **not** Material Design’s default breakpoint numbers for `md` / `lg` / `xl`.

**Why:** This is a deliberate choice so **layout, density, and overlays behave correctly on viewports smaller than a typical iPad**—phones, small tablets, and narrow windows—**before** we treat the UI as “tablet / desktop.” In practice:

- **`sm` at 600px** separates compact, touch-first patterns from wider layouts. It sits **below iPad portrait (~768px)**, so sub–iPad widths get the intended responsive treatment (e.g. collapsed chrome, full-width dialogs where we apply them) without waiting until Material’s shorter `md` band.
- **`md` at 1024px** aligns with **small laptop / iPad landscape–class** widths as the first “comfortable product UI” step.
- **`lg` / `xl` / `xxl`** continue the desktop scale (e.g. 1440 / 1920 / 2560) for large monitors and design-frame widths.

Consumers should treat these values as **design-system contracts**, not as “whatever MUI ships by default.”

---

## Dialog `maxWidth` labels vs theme breakpoint **names** (naming / QA clarity)

MUI’s Dialog `maxWidth` prop uses labels **`sm` | `md` | `lg` | `xl` | `false`** as **dialog size presets**, not as aliases for “use `theme.breakpoints.sm` width.” Theme overrides can map each preset to **any** pixel `maxWidth`.

In this kit, **`dialog.tsx`** maps paper presets to **`breakpointValues`** so dialog widths stay on the same token scale, but the **MUI label** and the **token key** can differ (e.g. preset `md` → `breakpointValues.sm` px). That avoids huge modal papers on small presets but can confuse QA or devs who assume **`maxWidth="lg"` === layout `lg` (1440px)**.

**Ways to resolve the confusion:**

1. **Document the mapping** (lowest effort): In design docs and/or a comment above the overrides, add a small table: `Dialog maxWidth` → `maxWidth` in px → which `breakpointValues` key (if any). Set expectation: _dialog sizes are content widths, not viewport breakpoint names._
2. **Align names with pixels 1:1** (breaking / visual change): Override `paperWidthSm` → `sm` px, `paperWidthMd` → `md` px, etc., so the string `md` always means 1024px paper. Dialogs become much wider at `md`/`lg`; only do this if product agrees.
3. **Avoid overloaded words in UX copy**: In Storybook / Figma, call dialog sizes **“S / M / L / XL (content)”** instead of reusing **md/lg** language next to layout breakpoints.
4. **Custom sizes**: For critical flows, prefer explicit `sx` / `PaperProps.sx` with a **design token** (e.g. `maxWidth: 720`) named in tokens, not `maxWidth="lg"` alone.

Recommended default for this repo: **(1) + (3)**; use **(2)** only if the team wants strict parity between Dialog prop strings and `theme.breakpoints.*` widths.

### Dialog `maxWidth` → pixels (implemented mapping)

Use this table in reviews and Figma annotations. **Layout** breakpoints (`sm` = 600px viewport step, `md` = 1024px, …) are **not** the same as these **MUI preset strings**.

| MUI `maxWidth` | Paper max width (px) | Source in theme       | Notes                                         |
| -------------- | -------------------: | --------------------- | --------------------------------------------- |
| `xs`           |          MUI default | not overridden        |                                               |
| `sm`           |          MUI default | not overridden        |                                               |
| `md`           |              **600** | `breakpointValues.sm` | Preset says “md”, pixel width is **sm** token |
| `lg`           |             **1024** | `breakpointValues.md` | Preset “lg” → **md** token                    |
| `xl`           |             **1440** | `breakpointValues.lg` | Preset “xl” → **lg** token                    |

**UX / docs (approach 3):** In Storybook and design specs, refer to these as **M (content)**, **L (content)**, **XL (content)** with a footnote listing the underlying `maxWidth` prop for engineers.

---

## Related documentation

- [tailwind-to-open-ui-kit-migration.md](./tailwind-to-open-ui-kit-migration.md) — Lungo **Tailwind → Open UI Kit** process; use this file’s breakpoint table when translating responsive utilities to `sx`.  
- [open-ui-kit-vs-mui-layout.md](./open-ui-kit-vs-mui-layout.md) — how MUI applies breakpoint keys vs default Material.  
- [open-ui-kit-breakpoints-migration-plan.md](./open-ui-kit-breakpoints-migration-plan.md) — checklist when changing breakpoints in **Open UI Kit** source or auditing consumers.
