---
name: amc-development
description: Implement, diagnose, test, package, or publish changes in the Accessible Multimedia Controller repository. Use for AMC code and architecture work; do not use for generic media research or unrelated document audits.
---

# AMC development

Work in the canonical repository `D:\Projekty Codex\Accessible Multimedia Controller`.

## Orient before editing

1. Read the repository `AGENTS.md` completely and preserve unrelated user changes shown by `git status`.
2. Read `MAPA_KODU_PL.md` before searching broadly. Use its current feature section plus the numbered architecture section relevant to the task.
3. Search `TESTY_ZADANIA_PL.md` for the affected command, screen, feature, or AMC test identifier instead of loading the whole historical file.
4. Read only the relevant `PROJEKT_*`, current `PLAN-*`, risk-register, and release-history files. Treat older instructions as history when a newer map, implementation, or test contradicts them.

## Implement against the real state model

- Distinguish the media or session that owns an operation from the screen currently visible when its asynchronous result arrives.
- Preserve selection, focus, and navigation context when refreshing a list. Update only the data that actually changed when practical.
- Keep user-facing text separate from internal IDs, enum values, object representations, paths, and command names.
- Do not silently broaden a focused change into an architecture migration or integration rewrite.
- Never place account data, OAuth tokens, local collections, private recordings, or user logs in source control or release packages.

## Verify in proportion to the change

- Run the narrowest existing smoke-test selector that exercises the changed behavior first.
- For changes shared by several views or sessions, test a representative variant of every affected path; a single green variant is not proof of all variants.
- Validate a new regression test with a negative control or temporary mutation when feasible, so the test is known to fail for the broken behavior.
- Run `powershell -ExecutionPolicy Bypass -File .\build.ps1` for repository-wide verification when the scope warrants it. Use `-Publish` only when a package is actually requested.
- Keep source publication, GitHub release assets, package verification, program launch, live-account checks, real audio, and live NVDA checks as separate reported outcomes.
- Do not claim a live integration or audible result from mocks, fixtures, HTTP success, focus properties, or a passing build alone.

For user-interface or accessibility behavior, also use the `amc-accessibility-validation` skill.

