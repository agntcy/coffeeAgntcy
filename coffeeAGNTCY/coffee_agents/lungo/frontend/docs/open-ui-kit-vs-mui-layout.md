# Open UI Kit vs Material UI: layout, breakpoints, and responsiveness

This document summarizes how **`@open-ui-kit/core`** relates to **Material UI (MUI)** for responsive layout, spacing, and grid behavior.

**Breakpoint numbers:** Use **[open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md)** as the single source of truth for `theme.breakpoints.values`. This file explains *how* MUI uses those keys, and how they differ from **default** Material UI.

Sources: `@open-ui-kit/core` v1.x (MUI-based), upstream theme in [outshift-open/open-ui-kit](https://github.com/outshift-open/open-ui-kit) (`light-theme.tsx` / `dark-theme.tsx`, `common.tsx`), and MUI `@mui/system` breakpoint handling.

---

## Executive summary

| Area | Same as default MUI? | Notes |
|------|----------------------|--------|
| **Mechanism** | Yes | Both use MUI `createTheme`, `sx`, `Stack`, `Grid`, `useMediaQuery`, `theme.spacing`. |
| **Breakpoints** | **No** | Product scale is **`xs` → `xxl`** with kit-specific pixels (see [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md)). Default MUI uses different widths (e.g. `md: 900`, not `1024`). |
| **`xs` / `sm` in `sx`** | **Must exist in `theme.breakpoints.values`** | Per [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md), `xs`/`sm`/`md`/… are part of the contract. If a fork omits keys, MUI will not emit normal `min-width` rules for missing names—extend the theme rather than assuming defaults. |
| **Spacing (`theme.spacing`)** | **Mostly yes** | Kit theme typically does not replace MUI’s default spacing factory → default **8px per unit** unless you override. |
| **Gaps (`Stack` / flex gap)** | Same mechanism | Numeric values go through the same spacing/breakpoint resolution as MUI. |
| **Grid** | Same mechanism | Breakpoint props depend on **`theme.breakpoints`**. |
| **Typography / palette / shadows / `components`** | **No** | Kit-specific tokens and overrides; does not change spacing math but changes component defaults (padding, radius inside `Button`, etc.). |

---

## Breakpoints in detail

### Default Material UI (typical)

- **xs:** 0  
- **sm:** 600  
- **md:** 900  
- **lg:** 1200  
- **xl:** 1536  

### Open UI Kit (product contract)

Full ladder — **authoritative table:** [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md) (`xs` 0, `sm` 600, `md` 1024, `lg` 1440, `xl` 1920, `xxl` 2560).

Implications:

1. **`md` / `lg` / `xl` in this kit are not the same as default MUI** (e.g. kit `md` is **1024**, not 900; kit `lg` is **1440**, not 1200).  
2. **`sm` (600) is the step below `md` (1024)** — not the same as default MUI’s `md` (900) or default Tailwind’s `md` (768).  
3. Responsive objects like `{ xs: …, sm: …, md: … }` in `sx` require those keys to exist on **`theme.breakpoints.values`**; use the canonical table as the reference when auditing or merging themes.

---

## How MUI resolves responsive `sx` keys

MUI’s style pipeline treats a key as a breakpoint only if it appears in **`Object.keys(theme.breakpoints.values)`**. If a key is missing, it is not converted to a `@media (min-width: …)` rule in the usual way. The **product contract** includes all keys in [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md); older forks or partial merges should be checked so `sx` breakpoint keys match an installed theme.

---

## Margins, padding, gaps, Grid

### Margins and padding (`sx`, `m`, `p`, `mt`, …)

- Resolved through **`theme.spacing`** and the same **`sx`** pipeline as MUI.  
- **No difference** in *how* numbers map to CSS, given the same `spacing` config.

### `Stack` `spacing` / `gap`

- Uses the **same MUI components** (re-exported from `@open-ui-kit/core`) and **same theme**.  
- Responsive `gap` / `spacing` follows **`theme.breakpoints`** — same caveat: need valid keys (`xs`, `sm`, …) if you use them.

### `Grid` / `Grid2`

- **Same as MUI** for implementation.  
- Column breakpoint props (`xs={12}`, `md={6}`, …) use **`theme.breakpoints`**.  
- If `xs`/`sm`/… are missing on a given theme build → inconsistent behavior for those props; align with [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md).

---

## Differences beyond breakpoints

### Typography

Open UI Kit supplies a **custom** `typography` object (e.g. Inter / Sharp Sans, explicit `fontSize` / `lineHeight` in px, extra variants). This is **not** the default MUI Roboto scale.

### Shape (border radius)

Often **inherits MUI defaults** unless the kit or your app overrides `theme.shape`.

### Shadows and palette

**Kit-specific** shadow arrays and palettes (including CSS variable layers in some setups).

### Component defaults (`theme.components`)

Many **`Mui*`** `styleOverrides` / `defaultProps` change **intrinsic** padding, sizes, and radii inside inputs, buttons, dialogs, etc. That is **orthogonal** to `theme.spacing(1)` but affects how dense the UI feels.

### Hardcoded media queries in the kit

Some mixins use **literal** `px` in `@media` (e.g. `min-width: 600px`) instead of `theme.breakpoints.up('sm')`. Those can **drift** from your theme if you add or change `sm`.

---

## Suggestions: using breakpoints consistently

### Design principle

- Treat **[open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md)** as the **single source of truth** for pixel values; do not introduce alternate `sm`/`md` numbers in app docs or configs without updating that file first.

### When forking or merging themes

1. **Upstream / fork of `@open-ui-kit/core`**  
   - Keep `createTheme({ breakpoints: { values: … } })` aligned with the canonical table in **light** and **dark** (or shared factory).

2. **Application-only merge (e.g. Lungo)**  
   - If you merge breakpoints in app code, use `createTheme(kitTheme, { breakpoints: { values: { … } } })` with the **same** ordered `values` as [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md) unless product explicitly documents a deviation.

### Responsive `sx` and JS queries

- **`md` = 1024px** in this product, not default MUI’s 900px.  
- Use **`between('sm','md')`** for the **600–1023px** band when that middle step matters.  
- Prefer **`theme.breakpoints.up('sm')`** over hardcoded **`600px`** in CSS when tying layout to `sm`.

### Legacy themes or partial keys

If a consumer runs against a theme that **omits** keys from the canonical table, `sx` using those keys will not behave as documented. **Fix the theme** to match [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md), or temporarily avoid those keys in `sx` / Grid props.

---

## Related files in this repo

- [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md) — canonical `theme.breakpoints.values`.  
- `src/contexts/OpenUiKitThemeBridge.tsx` — wraps `ThemeProvider` from `@open-ui-kit/core` with Lungo light/dark (`isDarkMode`).

---

## References

- [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md) — product breakpoint table.  
- [Material UI — Breakpoints](https://mui.com/material-ui/customization/breakpoints/)  
- [Open UI Kit repository](https://github.com/outshift-open/open-ui-kit)  
- MUI `@mui/system` — `createBreakpoints`, `handleBreakpoints` (responsive keys must exist in `theme.breakpoints.values`)
