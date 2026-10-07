#!/usr/bin/env python3
"""Report [[wikilinks]] that do not resolve to a note in the vault."""
import re, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
notes = {p.stem for p in root.rglob("*.md") if "_templates" not in p.parts}
code = re.compile(r"`[^`]*`")
link = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
bad = 0
for p in root.rglob("*.md"):
    if "_templates" in p.parts:
        continue
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        for target in link.findall(code.sub("", line)):
            if target.strip().split("/")[-1] not in notes:
                print(f"{p.relative_to(root)}:{n}: broken link [[{target}]]")
                bad += 1
print(f"{bad} broken link(s)")
sys.exit(1 if bad else 0)
