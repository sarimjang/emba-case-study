# Domain Docs

This repo uses a single-context domain-doc layout.
Engineering skills should treat the repo root as the primary context boundary.

## Before exploring, read these

- `CONTEXT.md` at the repo root, if it exists.
- `docs/adr/`, if it exists.

If these files do not exist, proceed silently.
Do not flag their absence during ordinary task work.
Domain docs can be created later when domain terms or architectural decisions need to be recorded.

## File structure

Expected single-context layout:

```text
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-example-decision.md
│   └── 0002-example-decision.md
└── scripts/
```

## Use the glossary's vocabulary

When output names a domain concept, use the term as defined in `CONTEXT.md` when that file exists.
Do not drift to synonyms the glossary explicitly avoids.

If the concept is not in the glossary yet, note the gap only when it affects the task.

## Flag ADR conflicts

If output contradicts an existing ADR, surface the conflict explicitly instead of silently overriding the decision.
