"""Prompt templates. All model-facing text lives in this package, nowhere else.

Templates use {{placeholders}} so that JSON examples inside a prompt can keep
their single braces and stay readable.
"""

from __future__ import annotations

import re

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def render(template: str, **values: object) -> str:
    """Substitute {{name}} placeholders. Unknown placeholders are an error."""
    missing: list[str] = []

    def substitute(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            missing.append(key)
            return match.group(0)
        return str(values[key])

    out = PLACEHOLDER.sub(substitute, template)
    if missing:
        raise KeyError(f"Prompt template is missing values for: {sorted(set(missing))}")
    return out
