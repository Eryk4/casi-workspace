# CASI Workspace — Project Instructions

This repository is the canonical project for the CASI Workspace application.

CASI is intended to become a real operational SaaS system, not a demo, mockup, or temporary prototype.

The application should be built with long-term scalability, maintainability, modularity, cost control, and future infrastructure flexibility in mind.

---

# 1. Workspace Rule — Hard Rule

Always use the following directory as the default working directory for this project:

`C:\Users\erykl\OneDrive\Dokumenty\CASI Workspace`

Rules:

- Do not implement, analyze, or edit code outside this directory.
- If a thread, terminal, or tool starts in another directory, switch context to this directory before doing meaningful work.
- Treat this repository as the source of truth for the CASI Workspace project.

---

# 2. Product Direction

CASI is a business workspace for company operations, automation, documents, invoices, tasks, assistants, reporting, and future AI-powered modules.

The long-term goal is to create a scalable SaaS-style application that can grow into multiple modules and serve real business clients.

Every important decision should support:

- clarity,
- scalability,
- speed of use,
- maintainability,
- modular expansion,
- cost awareness,
- production readiness,
- future infrastructure flexibility.

Do not optimize only for a quick visual result if it harms the long-term structure of the application.

---

# 3. Instruction Priority

Use these instructions with common sense.

There are three levels of rules in this file:

## Hard Rules

Hard rules must be followed unless the user explicitly instructs otherwise.

Examples:

- work only inside the CASI Workspace directory,
- do not mix the new production frontend with the legacy prototype,
- do not silently break business logic,
- keep the AppShell and navigation architecture consistent.

## Architectural Preferences

Architectural preferences should guide decisions, but they are not absolute blockers.

Examples:

- prefer portability,
- prefer modular AI provider design,
- prefer reusable components,
- prefer cost control through automation intensity instead of disabling features.

If a preference conflicts with a practical MVP need, choose the practical solution and explain the trade-off.

## Current Product Assumptions

Current assumptions describe the best-known direction today.

They may change later.

Examples:

- KSeF checking may start as an on-demand action in the MVP,
- DigitalOcean AI may be considered later,
- Make.com may support integrations but should not necessarily hold all core logic forever.

Do not treat current assumptions as permanent final architecture unless explicitly confirmed.

---

# 4. Final Frontend Direction — Hard Rule

The final production frontend of CASI must be built as a separate Next.js/React application inside the `frontend/` directory.

The legacy frontend in `static/` is treated as:

- a working prototype,
- a reference source,
- a source of existing behavior,
- not the final production frontend.

Rules:

- Do not mix the new production frontend with legacy HTML/CSS/JS files.
- Do not redesign the legacy frontend as the final solution unless explicitly requested.
- Do not treat cosmetic changes to the legacy frontend as final product work.
- When building final product UI, prioritize the `frontend/` application.
- Build all new UI modules, components, routes, and styles in `frontend/` only.
- Treat `static/` as legacy backup, not as UI source of truth.
- Do not edit `static/` unless the user gives an explicit emergency instruction.
- Backend can temporarily keep serving `static/` legacy UI for compatibility.
- Legacy static serving can be disabled with `CASI_SERVE_LEGACY_STATIC=0` only after deploy is ready to serve `frontend/` as the main UI.

For final product work, prefer:

- Next.js,
- React,
- shared AppShell,
- central navigation config,
- reusable UI components,
- modular feature structure,
- clean API layer,
- scalable SaaS architecture.

---

# 5. Frontend Architecture Principle

CASI frontend must be:

- modular,
- predictable,
- consistent,
- easy to extend with new modules,
- ready for real production use.

Do not treat UI changes as only visual tweaks.

Treat UI changes as architectural work when they affect:

- layout,
- navigation,
- module structure,
- reusable components,
- data flow,
- user workflows.

---

# 6. AppShell — Hard Rule

CASI should use a single shared AppShell across the production frontend.

The AppShell is the base layout and should not be bypassed by individual modules.

The AppShell should include:

- left sidebar,
- topbar,
- main content area,
- optional right panel only when useful.

Layout rules:

- sidebar is the primary navigation on desktop,
- sidebar may collapse on smaller screens,
- topbar is always present,
- content area fills the remaining space,
- modules should render inside the AppShell,
- modules should not define their own full-page layout unless there is a clear architectural reason.

---

# 7. Navigation System

Navigation should be centralized.

Do not hardcode menus in many unrelated places.

The production frontend should use a central navigation configuration for main modules.

Each module should define, when applicable:

- id,
- label,
- route,
- icon,
- component or page reference,
- optional children,
- optional permissions or feature flags later.

Example module direction:

- Pulpit,
- Asystent Szefa,
- Asystent Firmowy,
- Dokumenty,
- Faktury,
- Kasa,
- CRM,
- Raporty,
- Ustawienia.

Rules:

- sidebar should be generated from the navigation config,
- routing should match this config,
- do not duplicate navigation logic across modules,
- do not create separate competing navigation systems.

---

# 8. Sidebar

Sidebar is the primary navigation element.

Rules:

- contains all main modules,
- supports icons and labels,
- supports future grouping,
- active state must be clearly visible,
- should support collapsed mode with icons only.

Do not:

- move primary navigation to the topbar,
- duplicate sidebar navigation elsewhere,
- hide important modules in isolated local menus without a reason.

---

# 9. Topbar

Topbar is contextual, not the primary navigation.

Topbar may include:

- current module title,
- search,
- notifications,
- user profile,
- contextual actions for the active module.

Do not overload the topbar with primary navigation.

---

# 10. Content Area

The content area is where modules render.

Rules:

- each module renders inside the shared AppShell,
- modules should use consistent spacing,
- modules should use predictable layout patterns,
- avoid one-off page structures unless they solve a real problem,
- dense business data should remain readable and easy to scan.

---

# 11. Visual Style Direction

CASI should use a clean, modern, light SaaS-style interface.

Core principles:

- clean,
- minimal,
- high readability,
- spacing over decoration,
- professional but not heavy,
- operational dashboard feel,
- calm interface for everyday work.

Preferred visual direction:

- light background,
- subtle cards,
- limited accent colors,
- readable tables,
- clear hierarchy,
- strong but simple titles,
- consistent spacing,
- minimal visual noise.

Avoid:

- heavy gradients,
- random decorative elements,
- inconsistent shadows,
- overcrowded cards,
- redesigns that only change colors without improving structure.

---

# 12. Component System

UI should be built with reusable components.

Core reusable components should include, where useful:

- Button,
- Card,
- Table,
- Input,
- Modal,
- Badge,
- Tabs,
- Dropdown,
- SidebarItem,
- Topbar,
- PageHeader,
- EmptyState,
- LoadingState,
- ErrorState,
- StatusBadge,
- FilterBar.

Rules:

- reuse existing components when they fit,
- keep components small and focused,
- keep business logic out of generic UI components,
- avoid duplicating components for small visual differences,
- prefer extending component variants over creating many similar components.

---

# 13. Module Structure

Each module should follow a consistent structure when possible:

- header with title and actions,
- filters or controls when needed,
- main content such as table, cards, dashboard, or workflow view,
- secondary panels when useful,
- empty, loading, and error states.

Do not make every module look like a completely separate application unless there is a strong product reason.

Consistency matters because CASI is expected to grow.

---

# 14. Redesign Rule

When asked to redesign UI, do not treat it as a minor cosmetic task.

A real redesign should usually improve:

- layout structure,
- information hierarchy,
- component structure,
- navigation consistency,
- usability,
- readability,
- visual system.

Do not present these as a full redesign:

- only changing card sizes,
- only changing spacing,
- only changing colors,
- slightly rearranging tiles,
- changing shadows without improving the layout.

If a task asks for a major redesign, first consider whether the AppShell, navigation, and module structure need to change before polishing individual components.

---

# 15. Change Strategy

When doing significant frontend work, prefer this order:

1. AppShell,
2. navigation,
3. module wrapping,
4. layout consistency,
5. component consistency,
6. visual styling,
7. fine polish.

If the AppShell or navigation is wrong, fix that before polishing individual cards.

For small tasks, use judgment and do not over-engineer.

---

# 16. Business Logic Safety — Hard Rule

Do not silently break business logic.

Be especially careful with:

- API calls,
- database fields,
- form logic,
- filters,
- calculations,
- integrations,
- permissions,
- authentication,
- data ownership,
- invoice logic,
- payment status logic,
- client-specific data.

Do not change these unless:

- the user explicitly asks for it,
- the current task clearly requires it,
- or the existing implementation is broken and must be fixed.

If a change may affect business logic, explain the assumption or trade-off.

---

# 17. Data and API Layer Direction

Frontend should communicate with backend through a clean API layer.

Preferred approach:

- avoid scattering fetch calls across random components,
- use shared API utilities or service functions,
- keep API contracts predictable,
- keep module-specific data access inside module services when appropriate,
- do not couple UI components directly to infrastructure provider details,
- design API contracts so backend or hosting migration is possible later.

This is a preference, not a reason to block small MVP progress.

If a simpler implementation is chosen temporarily, keep it easy to refactor later.

---

# 18. Infrastructure Direction

CASI should be designed with future scalability and infrastructure portability in mind.

Possible infrastructure options may include:

- DigitalOcean,
- Fly.io,
- Google Cloud,
- Vercel,
- other suitable providers.

No provider should be treated as the final permanent choice unless explicitly confirmed.

DigitalOcean AI may become useful later as part of the AI/cloud infrastructure, but it is not currently a final architectural decision.

Rules and preferences:

- avoid unnecessary vendor lock-in where reasonably possible,
- keep core business logic independent from hosting provider,
- isolate provider-specific logic in adapters, services, configuration, or infrastructure layers,
- do not scatter provider-specific assumptions across UI components or business modules,
- design the app so future migration is possible without rewriting the whole product.

Important:

Do not overcomplicate the MVP only to avoid every possible form of vendor lock-in.

Portability is important, but practical progress is also important.

Use a balanced approach.

---

# 19. AI Provider Direction

AI usage should be modular and provider-aware.

OpenAI may be used.

Other providers may be considered later, including DigitalOcean AI or other AI infrastructure options if they become useful.

Preferences:

- keep AI calls behind a service layer,
- avoid calling AI providers directly from random UI components,
- store prompts, models, and provider configuration in predictable places,
- keep room for multiple AI providers in the future,
- track AI usage in a way that can support cost monitoring later,
- avoid hard-coding one provider so deeply that changing it later becomes unnecessarily difficult.

Current assumption:

DigitalOcean AI should be treated as a possible future infrastructure or AI tooling option, not as a final committed architecture.

Do not assume DigitalOcean AI is a separate final LLM provider unless explicitly confirmed later.

---

# 20. Automation and Cost-Control Direction

CASI should preserve useful product functionality where possible.

Default cost-control philosophy:

Do not rely mainly on brutal feature cut-offs.

Prefer gradual reduction of automation intensity.

Examples:

- reduce polling frequency,
- delay low-priority background jobs,
- use queues,
- process non-critical jobs less often,
- move selected actions to manual or on-demand triggers,
- limit automation frequency by plan,
- prioritize important modules or clients,
- degrade intensity before fully disabling features.

The application should be able to adjust automation intensity depending on:

- cost,
- plan,
- system load,
- client package,
- module importance,
- user-triggered actions.

Important principle:

Preserve features where possible, but control costs through frequency, queues, priority, plan limits, and on-demand execution.

---

# 21. Background Jobs and Scheduled Work

Background work affects cost and scalability.

Preferences:

- avoid unnecessary constant polling,
- prefer event-driven or on-demand actions where practical,
- use scheduled jobs only when they provide real value,
- make background jobs idempotent where possible,
- add status tracking for long-running jobs,
- add error states and retry logic where needed,
- keep room for queues and priority levels,
- do not assume all clients need the same automation frequency.

For cost-sensitive modules, prefer configurable automation intensity.

---

# 22. KSeF and Invoice Module Direction

For the MVP, prefer an on-demand KSeF checking model unless the task explicitly requires scheduled automation.

Current MVP assumption:

- the user may click something like “Check KSeF now”,
- the system checks KSeF when requested,
- automatic checking is not required as the default MVP behavior.

Automatic KSeF checking can be added later as:

- a higher package feature,
- a scheduled daily automation,
- a more frequent automation for premium clients,
- a configurable background job.

Do not assume that KSeF must be checked every hour by default.

The invoice module should be designed so that different invoice sources can later feed into one consistent invoice database, including:

- KSeF,
- email invoices,
- uploaded files,
- Telegram submissions,
- OCR-based invoices,
- manually added invoices.

This direction should not block MVP work, but the data model should avoid unnecessary dead ends.

---

# 23. Make.com and External Automation Direction

Make.com may be used pragmatically as an integration and automation layer.

It may support:

- experiments,
- MVP workflows,
- external integrations,
- notifications,
- Telegram flows,
- email flows,
- prototyping,
- client-specific automation.

Long-term preference:

- the app should own the core data model,
- the app should own important business states,
- Make.com should not be the only permanent place where all core business logic exists,
- avoid designs that require manually duplicating a full Make scenario for every new client if the app can handle that logic centrally.

Important:

Do not reject Make.com solutions automatically.

Make.com is useful, especially for MVP and integrations.

Use it where it speeds up development, but avoid painting the product into a corner.

---

# 24. Logging, Auditability and Explainability

CASI should be designed with future logging, auditability, and explainability in mind.

Preferences:

- important automated actions should be traceable,
- AI decisions should include a short reason when useful,
- cost-heavy operations should be measurable,
- background jobs should expose clear statuses,
- errors should be understandable,
- logs should help diagnose what happened without forcing a developer to guess.

This is especially important for:

- invoices,
- KSeF,
- documents,
- OCR,
- AI actions,
- integrations,
- client-facing automations,
- permissions,
- payments,
- status changes.

Avoid silent failures.

---

# 25. Performance and Scalability

UI and architecture should be ready for growth.

Preferences:

- avoid hardcoded layouts,
- avoid fixed widths where unnecessary,
- support more modules in the future,
- design for expansion,
- keep large lists and tables ready for pagination, filtering, and search,
- avoid unnecessary re-renders,
- avoid duplicating data-fetching logic,
- keep API communication centralized where practical.

Do not over-engineer small features, but avoid choices that obviously block future growth.

---

# 26. Permissions and Multi-Client Future

CASI may later support multiple clients, organizations, users, roles, and packages.

Do not assume forever that:

- there is only one user,
- there is only one company,
- all users can see all data,
- all clients have the same features,
- all modules are enabled for everyone,
- all automations run at the same frequency.

When practical, keep room for:

- organizations,
- users,
- roles,
- permissions,
- feature flags,
- plan-based limits,
- client-specific configuration.

This does not mean every feature must implement full multi-tenant logic immediately.

It means avoid obvious architectural dead ends.

---

# 27. Error Handling

Errors should be visible and understandable.

Rules and preferences:

- do not fail silently,
- show useful error states in the UI,
- log technical details where appropriate,
- show user-friendly messages where appropriate,
- avoid exposing sensitive technical data to end users,
- keep retry paths possible for background jobs,
- make integration errors diagnosable.

---

# 28. Security and Sensitive Data

Be careful with sensitive data.

This may include:

- invoices,
- client data,
- emails,
- documents,
- API keys,
- tokens,
- OAuth credentials,
- personal data,
- financial data.

Preferences:

- do not expose secrets in frontend code,
- do not commit secrets to the repository,
- keep credentials in environment variables or secure configuration,
- isolate external provider credentials,
- keep client data separation in mind,
- avoid unnecessary logging of sensitive content.

If unsure whether something is sensitive, treat it carefully.

---

# 29. Working With Existing Code

Before making changes:

- inspect the current structure,
- understand whether the file belongs to legacy prototype or production frontend,
- avoid random edits across unrelated files,
- preserve existing working behavior unless the task requires changing it,
- prefer focused changes with a clear purpose.

When refactoring:

- keep the app working,
- avoid unnecessary rewrites,
- explain major structural changes,
- preserve business logic,
- keep future maintainability in mind.

---

# 30. What To Do When A Task Is Unclear

If a request is unclear:

- ask for clarification,
- or propose a structured solution,
- or make a reasonable assumption and state it clearly.

Do not:

- guess randomly,
- apply cosmetic changes and pretend the task is complete,
- invent hidden requirements,
- silently change business logic.

If the task probably affects architecture, state the architectural assumption before implementing when practical.

---

# 31. Codex Working Style

When working in this project, behave like a production engineer, not like a visual mockup generator.

Rules and preferences:

- think before editing,
- prefer durable structure over quick patches,
- avoid random changes across many files,
- keep changes aligned with AppShell, navigation, and module architecture,
- preserve future extensibility,
- avoid unnecessary provider lock-in,
- keep AI providers modular where practical,
- consider cost, queues, frequency, and on-demand execution for automation-related work,
- remember that KSeF checking in the MVP may be on-demand,
- explain meaningful trade-offs when choosing between speed and long-term architecture.

---

# 32. Practicality Rule

Do not over-engineer.

CASI should be future-ready, but the MVP still needs to move forward.

A good solution should balance:

- clean architecture,
- speed of implementation,
- cost,
- maintainability,
- future flexibility,
- user value.

Prefer simple architecture that can grow.

Avoid both extremes:

- chaotic quick patches,
- overcomplicated architecture that blocks progress.

---

# 33. Final Rule

CASI is not a demo UI.

It is a real operational system.

Every UI, architecture, automation, AI, and infrastructure decision should support:

- clarity,
- scalability,
- speed of use,
- future expansion,
- cost control,
- maintainability,
- production readiness,
- practical delivery.
