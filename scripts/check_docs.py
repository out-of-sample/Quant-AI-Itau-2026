#!/usr/bin/env python3
"""Valida links locais em Markdown sem depender de rede ou ferramenta externa.

O guarda confere destinos relativos de links Markdown e atributos HTML ``href``/``src``.
URLs externas e âncoras são deliberadamente ignoradas; seu objetivo é impedir que renomes e
reorganizações quebrem a navegação interna do repositório.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HTML_LINK = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
EXTERNAL_SCHEMES = {"data", "http", "https", "mailto"}


def _without_fenced_code(text: str) -> str:
    kept: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = (
            "```" if stripped.startswith("```") else "~~~" if stripped.startswith("~~~") else None
        )
        if marker:
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if fence is None:
            kept.append(line)
    return "\n".join(kept)


def _normalize(raw: str) -> str | None:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    elif " " in target:
        target = target.split(maxsplit=1)[0]

    parsed = urlsplit(target)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES or target.startswith("#"):
        return None
    path = unquote(parsed.path)
    return path or None


def broken_links(markdown: Path, root: Path) -> list[tuple[str, Path]]:
    try:
        text = markdown.read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return []

    text = _without_fenced_code(text)
    raw_links = [*MARKDOWN_LINK.findall(text), *HTML_LINK.findall(text)]
    broken: list[tuple[str, Path]] = []
    for raw in raw_links:
        normalized = _normalize(raw)
        if normalized is None:
            continue
        destination = (
            root / normalized.lstrip("/")
            if normalized.startswith("/")
            else markdown.parent / normalized
        )
        destination = destination.resolve()
        if not destination.exists():
            broken.append((raw, destination))
    return broken


def main(argv: list[str]) -> int:
    root = Path.cwd().resolve()
    failed = False
    for filename in argv:
        markdown = Path(filename)
        for raw, destination in broken_links(markdown, root):
            failed = True
            print(f"{markdown}: link local inexistente: {raw!r} -> {destination}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
