# Migration guide: Tailwind → Open UI Kit + Material UI

This document is the **authoritative process** for migrating Lungo frontend components from **Tailwind utility classes** to **Open UI Kit** (`@open-ui-kit/core`) and **Material UI** primitives. Follow the **Goals**, **Principles**, and **Step-by-step** sections below for each component or subtree.

**Breakpoint single source of truth:** [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md) — all `sx` breakpoint keys (`xs`, `sm`, `md`, …) and any `theme.breakpoints.*` usage must align with that table (`sm` **600**, `md` **1024**, `lg` **1440**, …). Default Tailwind `screens` (e.g. `sm` 640, `md` 768) **do not** match; replacing Tailwind with `sx` removes that mismatch.

**Related docs**

- [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md) — canonical `theme.breakpoints.values`  
- [open-ui-kit-vs-mui-layout.md](./open-ui-kit-vs-mui-layout.md) — how MUI resolves `sx` / Grid vs default Material  
- [open-ui-kit-breakpoints-migration-plan.md](./open-ui-kit-breakpoints-migration-plan.md) — checklist when **forking or changing** Open UI Kit theme breakpoints upstream

---

## Goals

- Use **design-system components** and **theme-driven styling** instead of ad-hoc Tailwind strings.
- Prefer imports from **`@open-ui-kit/core`** when the component exists there (it re-exports and extends MUI patterns).
- Keep **accessibility and behavior** intact; **visual defaults** come from the kit unless product asks otherwise.
- **By default, migrated code leaves no Tailwind** — no utility `className`s, no Tailwind-dependent `clsx`/`cn` patterns for layout or visuals in the migrated subtree (see Principle 5).

---

## Prerequisites in this repo

- App tree is wrapped with **`OpenUiKitThemeBridge`** (see `src/contexts/OpenUiKitThemeBridge.tsx`), which provides Open UI Kit’s **`ThemeProvider`** and light/dark switching via Lungo’s `ThemeContext`.
- Dependencies include **`@open-ui-kit/core`**, **`@mui/material`**, **`@emotion/react`**, **`@emotion/styled`**.
- **Tailwind** may remain in the build (e.g. PostCSS) while **unmigrated** files still use it; **a component that has been migrated** should not retain Tailwind in that file by default (Principle 5). Any exception is **stakeholder-approved** after explicit notice.

---

## Principles (mandatory)

### 1. Function first; kit defaults for visuals

When migrating a component:

1. **Understand behavior** — interactions, state, keyboard, focus, loading/error states, layout role (landmark regions, labels).
2. **Choose the right primitives** — prefer **Open UI Kit** exports (`Button`, `Dialog`, `Stack`, `TextField`, `Header`, etc.); use **`Box`**, **`Stack`**, **`Typography`** for layout and text when no higher-level kit component fits.
3. **Do not port old Tailwind styling by default** — avoid recreating previous colors, paddings, margins, border widths, radii, shadows, or arbitrary pixel values unless explicitly requested.
4. **Start from kit/MUI defaults** — use default props, `variant`, `color`, and minimal `sx` only where required for structure (e.g. `flex: 1`, `minWidth: 0`).
5. **Overrides later** — custom tokens, CSS variables, or pixel-perfect match to the old UI happen only when **stakeholders ask** for adjustments.

While doing the above, **remove Tailwind from the migrated component by default** and only retain it after explicit approval — see **Principle 5**.

**Rationale:** The migration is a **design-system alignment**, not a CSS translation layer.

---

### 2. Light and dark mode

- **Assume both modes** for any UI that stays visible in the shell (navigation, chrome, dialogs, forms, tables).
- Rely on **Open UI Kit / MUI theme** (`palette`, `colorSchemes`, component defaults) so components **adapt automatically** where the kit supports it.
- If a pattern **does not** have a clear light/dark treatment in the kit (e.g. a one-off custom surface, chart, or third-party widget), **stop and ask** whether to:
  - use a kit **`Paper`** / **`Card`** / **`Banner`** wrapper,
  - use **`sx`** with theme palette keys (`background.paper`, `text.primary`, …),
  - or keep a **documented exception** (e.g. fixed dark panel) with explicit approval.

---

### 3. Missing piece in Open UI Kit → check Material UI

If Open UI Kit does **not** expose a suitable component for a needed pattern:

1. **Search `@mui/material`** (and **`@mui/lab`** if already a dependency) for the closest match.
2. **Prefer importing from `@open-ui-kit/core`** when the same symbol is re-exported there (single import path, consistent theme).
3. If using **MUI-only** components, **document the gap** (what’s missing in the kit, which MUI component we used) so we can track upstream kit additions or wrappers later.

**Communicate:** File a short note (issue or comment in the migration PR) listing **kit gap + MUI fallback**.

---

### 4. Missing in both → composite or future kit component

If neither Open UI Kit nor MUI provides a close match:

1. **Recommend building a small composite** from **MUI building blocks**: `Box`, `Stack`, `Typography`, `Button`, `IconButton`, `TextField`, `Divider`, `Paper`, etc., following kit typography and spacing.
2. **Optionally** extract a **local** reusable component under `src/components/…` with a clear name and props.
3. **Longer term:** propose an **Open UI Kit–style** contribution (upstream or internal wrapper) if the pattern repeats across products.

---

### 5. No Tailwind in migrated code (default)

**Default rule:** When a component (or subtree) is treated as **migrated**, it should contain **no Tailwind-related styling**:

- No **`className`** strings using Tailwind utilities (`flex`, `p-4`, `sm:…`, arbitrary values, etc.).
- No **Tailwind-only** helpers used for those concerns (e.g. `tailwind-merge` / `cn()` **for** utility classes) in that component, unless product has approved an exception.
- Prefer **`sx`**, **`styled()`**, kit/MUI props (`spacing`, `variant`), and **theme** tokens instead.

**If Tailwind seems necessary** (rare examples: a plugin-only feature with no MUI equivalent yet, or a hard constraint from a third-party snippet):

1. **Do not** leave Tailwind in place silently.
2. **Stop and notify** stakeholders with a short rationale and options (e.g. pure `sx`, small CSS module, MUI `keyframes`, refactor third-party markup).
3. Only keep Tailwind after **explicit approval**; document the exception in the PR (file + reason).

**Scope note:** Other files in the repo may still use Tailwind until their own migration; Principle 5 applies per **migrated** component/file, not to the whole app on day one.

---

## Step-by-step: migrating one component

### Step A — Analysis

- [ ] List **DOM role** and **ARIA** expectations (dialog, menu, landmark, live region).
- [ ] List **states**: loading, error, empty, disabled, open/closed.
- [ ] Note **responsive** behavior (collapse, scroll, overflow); map Tailwind `sm:`/`md:`/`lg:` to **theme keys** using [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md) (not Tailwind’s default px).
- [ ] Identify **Tailwind-only** tricks (arbitrary values, `group-*`, plugins) that need a non-Tailwind equivalent.

### Step B — Component mapping

| Need | Look here first | Then |
|------|-----------------|------|
| Layout rows/columns | `Stack`, `Box` | `Grid` / `Grid2` |
| Top app chrome | Kit `Header` / MUI `AppBar` + `Toolbar` | `Box` + `Stack` if minimal |
| Actions | `Button`, `IconButton`, `Menu` | MUI docs |
| Feedback | `Dialog`, `Snackbar`/`Toast` (if kit), `Alert`, `CircularProgress` | MUI |
| Forms | `TextField`, `Select`, `Checkbox`, `Switch` | MUI |
| Data display | Kit `Table`, `Typography`, `Chip` | MUI |

Use **`import { … } from '@open-ui-kit/core'`** when the symbol exists in the kit’s public API.

### Step C — First implementation (defaults only)

- Replace **structural** `div`/`span` with **`Box`**, **`Stack`**, **`Typography`** as appropriate.
- Replace **buttons/inputs** with kit/MUI components with **default** `variant`/`size`/`color`.
- **Remove all Tailwind** from the migrated subtree (Principle 5): strip utility `className`s and Tailwind-specific composition; replace with `sx` / theme. If something appears to **require** Tailwind, escalate before merging.
- Avoid inline **legacy CSS variables** unless needed for temporary coexistence (prefer theme palette after override pass).

### Step D — Accessibility pass

- [ ] Focus order and visible focus ring (MUI defaults).
- [ ] `aria-*` and labels preserved or improved (`aria-label`, `DialogTitle`, `Tooltip` + `IconButton`).
- [ ] Color contrast in **both** light and dark themes.

### Step E — Review with product

- Share **screenshots** (light/dark, key breakpoints).
- Collect **override requests** (spacing, brand colors, borders) as a **second** task list — do not bundle them into the first “default kit” pass without instruction.

### Step F — Cleanup

- [ ] Confirm **no Tailwind utilities** remain in the migrated file(s) (Principle 5); only documented, approved exceptions.
- [ ] Run `npm run check` (lint, format, typecheck) for the frontend package.
- [ ] If the component is a pattern worth repeating, add a **one-line note** in this doc’s “Migrated components” table (optional team habit).

---

## Tailwind concepts → MUI / Open UI Kit (reference)

| Tailwind habit | Typical replacement |
|----------------|---------------------|
| `flex`, `gap-*`, `items-*` | `Stack` (`direction`, `spacing`, `alignItems`, `justifyContent`) or `Box` + `sx` |
| `p-*`, `m-*`, `space-*` | `sx={{ p: 2, mt: 1 }}` or `Stack spacing={2}`; values use **`theme.spacing`** (often 8px per unit) |
| `w-full`, `h-screen`, `min-h-*` | `sx={{ width: '100%', height: '100%', minHeight: … }}` or layout props |
| `border`, `rounded-*` | Default on `Paper`, `Card`, `Button`; or `sx={{ border: 1, borderRadius: 1 }}` using theme |
| `text-sm`, `font-*` | `Typography` with `variant` / `component` |
| `sm:`, `md:`, `lg:` | `sx` with **`xs` / `sm` / `md` / `lg`** objects or `theme.breakpoints.up('sm')` — pixels per [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md) (`sm` 600, `md` 1024, `lg` 1440); do not assume Tailwind’s default breakpoints |
| `hover:`, `focus:` | `sx` pseudo-selectors `'&:hover'`, `'&.Mui-focusVisible'` or component `color` / `variant` |

---

## Import strategy

1. **Prefer** `@open-ui-kit/core` for anything it exports (`Box`, `Stack`, `Button`, `Tooltip`, …).
2. **Use** `@mui/material/...`** only when needed and not re-exported by the kit, or for types: `import type { SxProps, Theme } from '@mui/material/styles'`.
3. **Avoid** mixing duplicate providers — keep a **single** theme root (`OpenUiKitThemeBridge`).

---

## Tailwind vs migration scope

| Situation | Tailwind allowed? |
|-----------|-------------------|
| File / component **not yet** migrated | Yes — existing utilities may remain until that unit is migrated. |
| File / component **declared migrated** | **No** by default (Principle 5). |
| **Child** inside a migrated parent | **No** — migrate the child or extract; do not leave Tailwind in the migrated tree. |
| **Third-party** widget that injects its own classes | Usually leave vendor markup alone; wrap or theme via kit/MUI where possible. If we must add Tailwind around it, **notify and get approval**. |
| Implementer believes Tailwind is **the only** viable option | **Stop and notify**; do not merge Tailwind without approval. |

**End state for migrated UI:** **Open UI Kit + MUI + `sx`** (and plain CSS/CSS modules only if agreed), not Tailwind utilities for the same responsibilities.

---

## Escalation quick reference

| Situation | Action |
|-----------|--------|
| Unsure which kit component fits | List 2 options + recommendation; default to MUI composite with kit theme |
| Light/dark looks wrong with defaults | Ask: palette tweak vs `sx` override vs exception |
| Feature missing in kit | Use MUI; document gap (Principle 3) |
| Feature missing in MUI | Propose `Box`/`Stack` composite; document (Principle 4) |
| Breakpoint / `sx` key behavior | [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md) (values) + [open-ui-kit-vs-mui-layout.md](./open-ui-kit-vs-mui-layout.md) (MUI mechanics) |
| Tailwind seems required for a migrated piece | **Notify stakeholder** with options; no silent Tailwind (Principle 5) |

---

## Document history

- Initial version: migration principles and process for Lungo frontend (Tailwind → Open UI Kit + MUI).
- Extended: **Principle 5** — default **no Tailwind** in migrated code; exceptions only after explicit notice and approval; table for scope vs unmigrated files.
- Synced: **authoritative process** statement; breakpoint **single source of truth** → [open-ui-kit-breakpoints.md](./open-ui-kit-breakpoints.md); related-doc order and Tailwind vs product px called out explicitly.
