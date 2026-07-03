# CASI Frontend Architecture

This directory is the production frontend for CASI Workspace.

## Core Rules

- `src/layouts/AppShell.tsx` is the shared application shell for all production modules.
- `src/config/navigation.ts` is the single source of truth for primary modules, routes, sidebar labels, topbar actions, readiness labels, and primary API endpoints.
- `src/modules/*` contains module screens. Route files in `src/app/*/page.tsx` should stay thin and delegate to module components.
- `src/components/ui/*` contains reusable UI primitives. Keep business logic out of these components.
- `src/lib/api.ts` is the shared API entry point. Avoid scattering raw `fetch` calls across module components.

## Module Pattern

New modules should render inside the AppShell and follow this shape:

- header with title, description, status badge, and actions,
- optional readiness or workflow summary,
- compact KPI row,
- main work area with table/list/workflow,
- secondary panel only when it helps scanning or decisions,
- visible loading, empty, and error states.

For modules that are not migrated to live data yet, use `ModuleBlueprintPage` from `src/modules/shared/ModulePlaceholder.tsx`.
The legacy `ModulePlaceholder` export remains available for compatibility.

## Verification

Use these commands from `frontend/`:

```bash
npm.cmd run typecheck
npm.cmd run build
npm.cmd run dev
```

On Windows, `npm run build` uses `scripts/build-next.js` to avoid a Next.js build-worker filesystem race seen under OneDrive. Other platforms keep the normal Next.js build behavior.
