#!/usr/bin/env python3
"""Report [[wikilinks]] that do not resolve to a note, and ![[picture]] embeds that do not resolve to a file in Images/.
Also reports any link that crosses between the Unofficial/ section and the rest of the vault (they must stay separate)."""
import re, sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
notes = {p.stem: p for p in root.rglob("*.md") if "_templates" not in p.parts}
files = {p.name for p in root.rglob("*") if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")}
code = re.compile(r"`[^`]*`")
link = re.compile(r"(!?)\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
bad = 0; embeds = 0
def zone(path): return "unofficial" if "Unofficial" in path.relative_to(root).parts else "official"
for p in root.rglob("*.md"):
    if "_templates" in p.parts:
        continue
    fenced = False
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        for bang, target in link.findall(code.sub("", line)):
            t = target.strip()
            if bang and Path(t).suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
                embeds += 1
                if t.split("/")[-1] not in files:
                    print(f"{p.relative_to(root)}:{n}: missing picture ![[{t}]]"); bad += 1
                continue
            name = t.split("/")[-1]
            if name not in notes:
                print(f"{p.relative_to(root)}:{n}: broken link [[{target}]]"); bad += 1
            elif zone(p) != zone(notes[name]):
                print(f"{p.relative_to(root)}:{n}: link crosses the Unofficial/ boundary -> [[{target}]]"); bad += 1
print(f"{embeds} picture embeds checked; {bad} problem(s)")
sys.exit(1 if bad else 0)
