---
name: amc-accessibility-validation
description: Validate AMC desktop accessibility, keyboard behavior, UI Automation, focus, and NVDA output. Use for new or changed controls and for accessibility regressions; reserve exhaustive audits for major UI or release gates.
---

# AMC accessibility validation

Apply this skill to the Accessible Multimedia Controller repository after reading its `AGENTS.md`. Pair it with `amc-development` when code is being changed.

## Accessible output invariants

- Give every data-bound list, combo-box, table, tree, palette, and menu item an explicit user-facing accessible label and stable display text.
- Never expose a class name, default object string, record dump, enum identifier, property name, command ID, or technical path through UI Automation or NVDA.
- Keep the spoken label separate from the internal value. Explain neutral numeric choices, for example `1,00 razy — normalna prędkość`.
- Keep a shortcut out of the accessible name when accelerator metadata already exposes it, so NVDA does not repeat it.
- Announce the requested result or state change briefly. Do not add progress chatter, duplicated summaries, or technical diagnostics to ordinary speech.

## Keyboard, focus, and refresh

For every changed data-bound control, verify:

1. the initially selected item;
2. expanded choices and arrow-key movement;
3. Enter, Space, Escape, Tab and relevant application shortcuts;
4. selection and focus after an asynchronous refresh;
5. focus return after Save, Cancel, closing a dialog, or returning from a subview;
6. repeated reopening, including empty and populated states.

Do not restore focus unconditionally if the user moved elsewhere while an asynchronous operation was running. Do not repair speech ordering with arbitrary delays.

## Evidence ladder

Use only the levels needed for the risk, and state the highest level actually completed:

1. unit or smoke test of the state and handler;
2. UI Automation inspection of names, roles, states, selection, and focus;
3. keyboard test in the built application;
4. live NVDA test of the actual spoken result;
5. representative full-profile or integration fixture;
6. exhaustive GUI harness or independent repeated audit for a major UI change or release gate.

A zero-violation automated scan is not proof of accessibility. UI Automation properties do not prove what NVDA spoke. Mocks and tiny fixtures do not prove behavior with the user's full profile.

Search `TESTY_ZADANIA_PL.md` for the affected view and extend the existing scenario when possible. A regression test should be shown to fail under the previous broken behavior, preferably with a temporary mutation or other negative control.

Do not automatically invoke document, PDF, web-WCAG, checkout, or CDP-browser audit workflows merely because AMC work concerns accessibility.

