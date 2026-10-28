#!/usr/bin/env python3
"""Print a complete, deterministic template for a future AMC language."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from amc_wx_lite import i18n  # noqa: E402
from amc_wx_lite.shortcuts import Action  # noqa: E402
from amc_wx_lite.transport_parity import (  # noqa: E402
    TEMPLATE_KEYS,
    default_templates,
    template_labels,
)


def build_template() -> dict[str, object]:
    ui = {key: "" for key in sorted(i18n.catalogs()[i18n.POLISH])}
    legacy = i18n.legacy_english_catalog()
    commands = {
        action.value: {"name": "", "description": ""}
        for action in sorted(Action, key=lambda item: item.value)
    }
    return {
        "_meta": {
            "language": "language-tag",
            "name": "Language name shown to users",
            "instructions": (
                "Fill every value; preserve keys and placeholders in braces."
            ),
        },
        "ui": ui,
        "legacyUi": {key: "" for key in sorted(legacy["static"])},
        "legacyTemplates": {
            key: "" for key in sorted(legacy["templates"])
        },
        "messageTemplateLabels": {
            key: "" for key in TEMPLATE_KEYS
        },
        "messageTemplates": dict(default_templates(i18n.POLISH)),
        "commands": commands,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(build_template(), ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
