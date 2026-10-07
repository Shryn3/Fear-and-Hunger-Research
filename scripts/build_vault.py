#!/usr/bin/env python3
"""Build the Obsidian vault notes from wikitext fetched by fetch_wiki.py.

usage: build_vault.py RAW_DIR VAULT_DIR

Everything written is derived from the fetched wikitext (untrusted data, only ever
treated as text). Nothing is filled in from memory; gaps are left empty or flagged.
Run twice internally: pass 1 collects link targets, pass 2 resolves redirects + writes.
"""
import json, re, sys, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path

RAW = Path(sys.argv[1]); VAULT = Path(sys.argv[2])
WIKI = "https://fearandhunger.wiki.gg/wiki/"
API = "https://fearandhunger.wiki.gg/api.php"
LICENSE = "CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)"

# ----------------------------------------------------------------- raw pages
PAGES = {}
for f in RAW.glob("*.json"):
    if f.name.startswith("_"):
        continue
    d = json.load(open(f, encoding="utf-8"))
    d["fetched"] = __import__("datetime").date.fromtimestamp(f.stat().st_mtime).isoformat()  # day the page was fetched
    PAGES[d["title"]] = d

def norm(t):
    t = urllib.parse.unquote(t).replace("_", " ").strip()
    return t[:1].upper() + t[1:]

def fname(s):  # filesystem/Obsidian-safe note name
    s = re.sub(r'[\\/:*?"<>|#^\[\]]', "", s)
    return re.sub(r"\s+", " ", s).strip()

def wiki_url(title, frag=""):
    u = WIKI + urllib.parse.quote(norm(title).replace(" ", "_"), safe="_(),:'")
    return u + ("#" + urllib.parse.quote(frag.replace(" ", "_")) if frag else "")

# ----------------------------------------------------------------- wikitext -> markdown
TEMPLATES_SEEN = defaultdict(int)

def split_top(s, sep="|"):
    out, depth, cur, i = [], 0, "", 0
    while i < len(s):
        two = s[i:i + 2]
        if two in ("{{", "[["):
            depth += 1; cur += two; i += 2; continue
        if two in ("}}", "]]"):
            depth -= 1; cur += two; i += 2; continue
        if s[i] == sep and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += s[i]
        i += 1
    out.append(cur)
    return out

def strip_templates(s, ctx):
    out, i = "", 0
    while i < len(s):
        if s.startswith("{{", i):
            depth, j = 1, i + 2
            while j < len(s) and depth:
                if s.startswith("{{", j): depth += 1; j += 2
                elif s.startswith("}}", j): depth -= 1; j += 2
                else: j += 1
            body = s[i + 2:j - 2]
            parts = split_top(body)
            name = parts[0].strip().lower()
            TEMPLATES_SEEN[name] += 1
            if name == "text-shadow":
                out += strip_templates(parts[1], ctx) if len(parts) > 1 else ""
            elif name == "speculation":
                out += "\n\n> [!warning] The wiki marks the following as speculation.\n\n"
            elif name == "bug":
                out += " ⚠ *(known bug listed on the wiki)*"
            i = j
        else:
            out += s[i]; i += 1
    return out

def convert_table(block, ctx):
    rows, cur = [], None
    for line in block.split("\n")[1:]:
        line = line.rstrip()
        if line.startswith("|}"): break
        if line.startswith("|-"):
            if cur: rows.append(cur)
            cur = []; continue
        if line.startswith("|+"): continue
        if line.startswith("!") or line.startswith("|"):
            cells = re.split(r"\s*(?:!!|\|\|)\s*", line[1:])
            if cur is None: cur = []
            for c in cells:
                c = re.sub(r"^\s*(?:style|class|colspan|rowspan|width|align)=[^|]*\|(?!\|)", "", c)
                cur.append(c.strip())
        elif cur:
            if cur: cur[-1] += "\n" + line.strip()
    if cur: rows.append(cur)
    rows = [r for r in rows if any(r)]
    if not rows: return ""
    w = max(len(r) for r in rows)
    md = []
    for i, r in enumerate(rows):
        r = r + [""] * (w - len(r))
        md.append("| " + " | ".join(clean(re.sub(r"^(<br>)+", "", re.sub(r"\n+", "<br>", re.sub(r"(?m)^[*#]+\s*", "• ", c.strip()))), ctx, inline=True).replace("|", "\\|") for c in r) + " |")
        if i == 0: md.append("|" + "---|" * w)
    return "\n".join(md)

def clean(text, ctx, inline=False):
    t = re.sub(r"<!--.*?-->", "", text, flags=re.S).replace("&nbsp;", " ")
    t = strip_templates(t, ctx)
    # footnotes from <ref>
    def ref(m):
        attrs, body = m.group(1), m.group(2)
        name = re.search(r'name\s*=\s*"?([^"\s/>]+)', attrs or "")
        key = name.group(1) if name else None
        if body is None or not body.strip():
            if key and key in ctx["refs"]:
                return f"[^{ctx['refs'][key]}]"
            return ""
        ctx["n"] += 1; n = ctx["n"]
        if key: ctx["refs"][key] = n
        ctx["fn"].append((n, clean(body, dict(ctx, fn=[], refs={}, n=0), inline=True)))
        return f"[^{n}]"
    t = re.sub(r"<ref([^>]*?)/>", lambda m: ref(type("M", (), {"group": lambda self, i: m.group(1) if i == 1 else None})()), t)
    t = re.sub(r"<ref([^>]*)>(.*?)</ref>", ref, t, flags=re.S)
    # tables (not in inline mode)
    if not inline:
        def tbl(m): return "\n" + convert_table(m.group(0), ctx) + "\n"
        t = re.sub(r"\{\|.*?\n\|\}", tbl, t, flags=re.S)
    # image/file embeds (may contain nested links in the caption)
    def strip_files(x):
        out, i = "", 0
        while i < len(x):
            m = re.match(r"\[\[(?:File|Image):", x[i:], re.I)
            if m:
                depth, j = 1, i + 2
                while j < len(x) and depth:
                    if x.startswith("[[", j): depth += 1; j += 2
                    elif x.startswith("]]", j): depth -= 1; j += 2
                    else: j += 1
                i = j
            else:
                out += x[i]; i += 1
        return out
    t = strip_files(t)
    # links
    def link(m):
        inner = m.group(1)
        if re.match(r"(?i)(file|image|category|[a-z]{2,3}):", inner) and not inner.lower().startswith(("f&h",)):
            return ""
        target, _, disp = inner.partition("|")
        frag = ""
        if "#" in target: target, frag = target.split("#", 1)
        disp = disp or (target + (("#" + frag) if frag else ""))
        if not target.strip():
            return disp
        return ctx["link"](target, disp.replace("_", " ") if not _ else disp, frag)
    t = re.sub(r"\[\[([^\[\]]+)\]\]", link, t)
    t = re.sub(r"\[(https?://[^\s\]]+)\s+([^\]]+)\]", r"[\2](\1)", t)
    t = re.sub(r"\[(https?://[^\s\]]+)\]", r"<\1>", t)
    # inline html
    t = re.sub(r"<abbr title=\"([^\"]*)\">(.*?)</abbr>", lambda m: m.group(2) if not re.search(r"[A-Za-z]{3}", m.group(1)) or m.group(1).lower() in m.group(2).lower() else f"{m.group(2)} ({m.group(1)})", t, flags=re.S)
    t = re.sub(r"<br\s*/?>", " / " if inline else "  \n", t, flags=re.I)
    def bq(m):
        return "\n" + "\n".join("> " + l for l in m.group(1).strip().split("\n")) + "\n"
    t = re.sub(r"<blockquote[^>]*>(.*?)</blockquote>", bq, t, flags=re.S | re.I)
    t = re.sub(r"<gallery.*?</gallery>", "", t, flags=re.S | re.I)
    t = re.sub(r"<references\s*/?>", "", t, flags=re.I)
    t = re.sub(r"</?(font|small|div|span|center|big|u|s|sup|sub|tabber|nowiki|poem|p|abbr)[^>]*>", "", t, flags=re.I)
    t = re.sub(r"^(\*+)\s*", lambda m: "  " * (len(m.group(1)) - 1) + "- ", t, flags=re.M)
    t = re.sub(r"^(#+)\s*", lambda m: "  " * (len(m.group(1)) - 1) + "1. ", t, flags=re.M)
    t = re.sub(r"'''''(.+?)'''''", r"***\1***", t)
    t = re.sub(r"'''(.+?)'''", r"**\1**", t)
    t = re.sub(r"''(.+?)''", r"*\1*", t)
    t = re.sub(r"^\|-\|.*$", "", t, flags=re.M)  # tabber headers
    t = re.sub(r"^[:;]+\s*", "", t, flags=re.M)
    t = re.sub(r"__\w+__", "", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip() if not inline else re.sub(r"\s+", " ", t).strip()

# ----------------------------------------------------------------- page structure
def infobox(wt):
    m = re.search(r"\{\{New-Infobox(.*?)\n\}\}", wt, re.S)
    d = {}
    if m:
        cur = None
        for line in m.group(1).split("\n"):
            mm = re.match(r"^\|\s*([A-Za-z0-9_\-]+)\s*=\s*(.*)$", line)
            if mm: cur = mm.group(1); d[cur] = mm.group(2)
            elif cur and line.strip(): d[cur] += "\n" + line
    return d

def body_wo_infobox(wt):
    return re.sub(r"\{\{New-Infobox.*?\n\}\}", "", wt, count=1, flags=re.S)

def sections(wt):
    """-> lead, [(level,title,text)] using the raw wikitext."""
    wt = body_wo_infobox(wt)
    ms = list(re.finditer(r"^(=+)\s*(.*?)\s*\1\s*$", wt, re.M))
    lead = wt[:ms[0].start()] if ms else wt
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(wt)
        out.append((len(m.group(1)), m.group(2), wt[m.end():end]))
    return lead, out

EXCLUDE = re.compile(r"(?i)gallery|navigation|references|dialog|interaction|strateg|battle|location|mode|restrain|recruit|loot|drop|shop|walkthrough|fight|enemy|^music|soundtrack|sprite|quote|see also|external")

# ----------------------------------------------------------------- notes model
NOTES = {}          # name -> dict(folder, fm, body, sources)
TITLE2NOTE = {}     # normalized wiki title -> note name
SRC_USED = defaultdict(set)   # source note name -> set of citing note names

def src_name(title): return fname("Wiki - " + title)

def make_ctx(owner):
    ctx = {"fn": [], "refs": {}, "n": 0, "owner": owner, "targets": set()}
    def link(target, disp, frag=""):
        if "#" in target:
            target, frag = target.split("#", 1)
        # an anchor into "The Gods" that names a god we have a note for -> link to that note
        if norm(target) == "The Gods" and frag and norm(frag) in TITLE2NOTE and TITLE2NOTE[norm(frag)] != "The Gods":
            target, frag = frag, ""
            if disp.startswith("The_Gods#") or disp.startswith("The Gods#"): disp = norm(target)
        ctx["targets"].add(norm(target))
        key = norm(target)
        note = TITLE2NOTE.get(key)
        if note and note != owner:
            return f"[[{note}]]" if disp == note else f"[[{note}|{disp}]]"
        if note == owner:
            return disp
        return f"[{disp}]({wiki_url(target, frag)})"
    ctx["link"] = link
    return ctx

def footnotes(ctx):
    return "".join(f"\n[^{n}]: Wiki citation: {t}" for n, t in ctx["fn"])

def frontmatter(d):
    lines = ["---"]
    for k, v in d.items():
        lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)

def cite(title, owner):
    SRC_USED[src_name(title)].add(owner)
    return f"[[{src_name(title)}]]"

def page_body(title, owner, ctx, only=None, skip_titles=(), maxlevel=6, base=2):
    """Render lead + kept sections of a wiki page as markdown with a Source line per block."""
    p = PAGES[title]
    lead, secs = sections(p["wikitext"])
    out = []
    txt = clean(lead, ctx)
    if txt: out.append(txt + f"\n\n*Source: {cite(title, owner)}*")
    skip_level = None
    for lvl, st, text in secs:
        if skip_level is not None and lvl > skip_level: continue
        skip_level = None
        plain = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", st)
        if (only and plain not in only) or EXCLUDE.search(plain) or plain in skip_titles:
            skip_level = lvl; continue
        body = clean(text, ctx)
        if not body: continue
        out.append(f"{'#' * min(6, base + lvl - 2 + 1)} {plain}\n\n{body}\n\n*Source: {cite(title, owner)}*")
    return "\n\n".join(out)

# ----------------------------------------------------------------- skill tables
def parse_table_rows(block):
    """Wikitable -> (headers, rows of raw cell strings)."""
    lines = block.split("\n")
    headers, rows, cur = [], [], None
    for line in lines[1:]:
        if line.startswith("|}"): break
        if line.startswith("|-"):
            if cur is not None: rows.append(cur)
            cur = []; continue
        if line.startswith("!"):
            h = re.sub(r"^\s*(?:style|class)=[^|]*\|", "", line[1:]).strip()
            headers.append(h); continue
        if line.startswith("|") and not line.startswith("|+"):
            c = line[1:]
            c = re.sub(r"^\s*(?:style|class|colspan|rowspan)=[^|]*\|(?!\|)", "", c)
            if cur is None: cur = []
            cur.append(c.strip()); continue
        if cur: cur[-1] += "\n" + line
    if cur: rows.append(cur)
    return headers, [r for r in rows if r]

def skill_records(game, title, groups=("Contestant skills", "God Affinity skills", "New Game Plus", "Soul skills")):
    """-> list of dict(game, group, sub_head, name, link_target, symbol, cells{})."""
    wt = PAGES[title]["wikitext"]
    ms = list(re.finditer(r"^(=+)\s*(.*?)\s*\1\s*$", wt, re.M))
    recs, group = [], None
    for i, m in enumerate(ms):
        lvl, head = len(m.group(1)), m.group(2)
        end = ms[i + 1].start() if i + 1 < len(ms) else len(wt)
        if lvl == 2: group = re.sub(r"\[\[.*?\]\]", "", head).strip()
        seg = wt[m.end():end]
        tm = re.search(r"\{\|.*?\n\|\}", seg, re.S)
        if not tm or group not in groups:
            continue
        headers, rows = parse_table_rows(tm.group(0))
        headers = [re.sub(r"\s+", " ", h) for h in headers]
        for r in rows:
            if len(r) < 2: continue
            cells = dict(zip(headers, r))
            namecell = cells.get("Name", r[0])
            sym = re.search(r"\[\[File:Symbol ([^\].|]*?)\d?\.png", namecell)
            lm = re.search(r"\[\[(?!File:)([^\]|]+)(?:\|([^\]]+))?\]\]", namecell)
            plain = re.sub(r"\[\[File:[^\]]*\]\]|<br\s*/?>", "", namecell)
            plain = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", plain).strip()
            recs.append(dict(game=game, group=group, head=head, name=(lm.group(2) or lm.group(1)) if lm else plain,
                             target=lm.group(1) if lm else None, symbol=sym.group(1).strip() if sym else None,
                             cells=cells, list_title=title))
    return recs

# ----------------------------------------------------------------- build
def build(final):
    NOTES.clear(); SRC_USED.clear()
    targets_seen = set()

    GODS = {  # wiki title -> (note name, class, first game)
        "Gro-goroth": "Old God", "Sylvian": "Old God", "God of the Depths": "Old God", "Rher": "Old God", "Vinushka": "Old God",
        "Alll-mer": "Ascended God", "God of Fear and Hunger": "Ascended God",
        "Sulfur God": "Unspecified classification", "Logic": "Unspecified classification", "Per'kele": "Unspecified classification",
        "Iki Turso": "Unspecified classification",
        "Francóis": "New God", "Nilvan": "New God", "Valteil": "New God", "Tormented One": "New God",
        "Tormented One (F&H2)": "New God", "Betel": "New God", "Nas'hrah": "New God", "Heartless One": "New God",
        "Radiating One": "New God", "Tainted One": "New God", "Kaiser": "New God", "Yellow King": "New God",
        "Blight": "Blight", "Greater Blight": "Blight",
    }
    # entities that only have a section on "The Gods" (no page of their own in the fetched set)
    SECTION_ONLY = {"Mourning One": ("New God", "Mourning One"), "Vitruvia": ("Unspecified classification", "Vitruvia"),
                    "Yggaegetsu": ("Unspecified classification", "Yggaegetsu"),
                    "Unnamed fire god": ("Unspecified classification", "Unnamed fire god"),
                    "Unnamed wolf deity": ("Unspecified classification", "Unnamed wolf deity"),
                    "Unnamed rat deity": ("Unspecified classification", "Unnamed rat deity")}
    CHARS = ["Daan", "Abella", "O'saa", "Olivia", "Karin", "Pav", "Marcoh", "Levi", "Marina", "Samarie", "Tanaka", "Henryk",
             "Caligura", "August", "Cahara", "D'arce", "Ragnvaldr", "Enki", "Reila"]
    DOCS = ["Skin Bible - Gro-goroth", "Skin Bible - Sylvian", "Skin Bible - Vinushka (unedited)", "Skin Bible - Rher",
            "Skin Bible - Alll-mer", "Studies of Gro-goroth I", "Studies of Sylvian I", "God manifesto"]
    MECH = ["Hexen F&H1", "Hexen F&H2", "Soul stone", "Soul stone (F&H2)", "Rev", "Ritual Circles F&H2", "Marriage of Flesh"]
    GAMES = {"Fear & Hunger": "Fear & Hunger", "Fear & Hunger 2: Termina": "Fear & Hunger 2 Termina"}

    # soul note names are known from the Soul type page before anything else is built
    _swt = PAGES["Soul type"]["wikitext"]
    _ALT = {"Dominating": "Domination", "Enlightenment": "Enlightened"}
    SOUL_NOTES = set()
    for n in re.findall(r'<font color="orange">(\w+) soul</font>', _swt) + re.findall(r"^\* \'\'\'(\w+)\'\'\'", _swt, re.M):
        n = _ALT.get(n, n)
        SOUL_NOTES.add(f"{n} soul")
    for n in SOUL_NOTES: TITLE2NOTE[norm(n)] = n
    # --- register note names first (so links resolve) ---------------------------------
    for t in GODS:
        if t in PAGES: TITLE2NOTE[norm(t)] = fname(t)
    for t, (cls, nm) in SECTION_ONLY.items(): TITLE2NOTE[norm(t)] = fname(nm)
    for t in CHARS:
        if t in PAGES: TITLE2NOTE[norm(t)] = fname(t)
    for t in DOCS + MECH:
        if t in PAGES: TITLE2NOTE[norm(t)] = fname(t)
    for t, n in GAMES.items(): TITLE2NOTE[norm(t)] = n
    TITLE2NOTE[norm("The Gods")] = "The Gods"
    TITLE2NOTE[norm("The Hall of the Gods")] = "The Hall of the Gods"
    TITLE2NOTE[norm("Soul type")] = "Soul types"
    for alias, real in {"The Radiating One": "Radiating One", "The Tainted One": "Tainted One", "Tormented One (F&H1)": "Tormented One",
                        "Mourning One": "Mourning One", "God of Fear and Hunger": "God of Fear and Hunger",
                        "The Girl": "God of Fear and Hunger", "Girl": "God of Fear and Hunger", "The Sulfur God": "Sulfur God",
                        "Hexen": "Hexen F&H2", "Soul stone (F&H1)": "Soul stone", "Ritual circles F&H2": "Ritual Circles F&H2"}.items():
        if norm(real) in TITLE2NOTE: TITLE2NOTE[norm(alias)] = TITLE2NOTE[norm(real)]
    if final:
        red = RAW / "_redirects.json"
        if red.exists():
            for a, b in json.load(open(red)).items():
                if norm(b) in TITLE2NOTE and norm(a) not in TITLE2NOTE: TITLE2NOTE[norm(a)] = TITLE2NOTE[norm(b)]

    # --- skills: records and names ------------------------------------------------------
    recs = skill_records("F&H2", "Skills List F&H2") + skill_records("F&H1", "Skills List F&H1")
    base_count = defaultdict(set)
    for r in recs:
        r["base"] = fname(r["target"] if r["target"] and norm(r["target"]) != norm(r["name"]) and False else (r["target"] or r["name"]))
        # if the link target differs from the displayed name, the displayed name is what players see: keep display name
        if r["target"] and "(F&H" in r["target"]: r["base"] = fname(r["target"])
        else: r["base"] = fname(r["name"])
        base_count[r["base"]].add((r["game"], r["group"], r["head"]))
    for r in recs:
        if len(base_count[r["base"]]) > 1:
            who = re.sub(r"\[\[.*?\]\]|\(.*?\)|\s+", " ", r["head"]).strip() if r["group"] != "New Game Plus" else "NG+"
            if r["group"] == "Contestant skills":
                m = re.search(r"\[\[([^\]|]+)\]\]", r["head"]); who = m.group(1) if m else who
            gtag = r["game"]
            r["note"] = fname(f'{r["base"]} ({gtag} {who})' if "(F&H" not in r["base"] else r["base"])
        else:
            r["note"] = r["base"]
    # the wiki sometimes lists the same skill twice under one heading (stackable +1 skills): one note, both listings
    first, kept = {}, []
    for r in recs:
        key = (r["note"], r["game"], r["group"], r["head"])
        if key in first:
            first[key].setdefault("dups", []).append(r)
        else:
            first[key] = r; kept.append(r)
    recs = kept
    seen = defaultdict(int)  # different headings that still share a note name get numbered
    for r in recs:
        seen[r["note"]] += 1
        if seen[r["note"]] > 1: r["note"] += f" {seen[r['note']]}"
    for r in recs:
        TITLE2NOTE.setdefault(norm(r["target"] or r["name"]), r["note"]) if (r["target"] and "(F&H" in r["target"]) else None

    soul_of_group = {}
    skill_by_soul = defaultdict(list); skill_by_god = defaultdict(list); ngp_by_god = defaultdict(list)
    skill_by_char = defaultdict(list)
    GOD_ALIAS = {"Fear and Hunger": "God of Fear and Hunger"}
    for r in recs:
        if r["group"] in ("Contestant skills", "Soul skills"):
            m = re.search(r"\[\[([^\]|F][^\]|]*)\]\]\s*\((\w+) soul\)", r["head"])
            if m: r["char"], r["soul"] = m.group(1), m.group(2)
            else:
                m2 = re.search(r"\|50px\]\]\s*(\w+) soul", r["head"]); r["soul"] = m2.group(1) if m2 else None
                fm = re.search(r"\[\[File:([^\s]+) portrait", r["head"]); r["char"] = fm.group(1) if fm else None
            skill_by_soul[r["soul"]].append(r)
            if r["char"]: skill_by_char[r["char"]].append(r)
        elif r["group"] == "God Affinity skills":
            g = re.sub(r"\[\[.*?\]\]", "", r["head"]).strip()
            r["god"] = GOD_ALIAS.get(g, g); skill_by_god[r["god"]].append(r)
        elif r["group"] == "New Game Plus":
            r["god"] = r["symbol"];
            if r["symbol"]: ngp_by_god[r["symbol"]].append(r)

    def skill_note(r):
        ctx = make_ctx(r["note"]); c = r["cells"]
        game = r["game"]
        folder = {"Contestant skills": "Skills/Soul", "Soul skills": "Skills/Soul", "God Affinity skills": "Skills/Divine",
                  "New Game Plus": "Skills/New Game Plus"}[r["group"]]
        fm = dict(type="skill", game=game, category=r["group"], aliases=[r["name"]] if r["name"] != r["note"] else [],
                  tags=["skill", "f&h1" if game == "F&H1" else "f&h2"])
        rows = []
        def row(label, key):
            v = c.get(key)
            if v is not None and clean(v, ctx, inline=True) not in ("", "-"):
                rows.append(f"| **{label}** | {clean(v, ctx, inline=True)} |")
        row("Description", "Description"); row("Effect", "Effect"); row("Cost", "Cost"); row("Success rate", "Success Rate")
        row("Unlock requirement", "Unlock Requirement")
        head = [f"# {r['name']}", "", ""]
        rel = []
        if r["group"] == "God Affinity skills":
            gnote = TITLE2NOTE.get(norm(r["god"]), None)
            fm["granted_by"] = f"[[{gnote}]]" if gnote else r["god"]
            rel.append(f"**Granted by:** {ctx['link'](r['god'], r['god'])} (god-affinity skill, {game})")
        elif r["group"] in ("Contestant skills", "Soul skills"):
            soul = f"{r['soul']} soul" if r["soul"] else None
            fm["soul"] = f"[[{soul}]]" if soul else None
            if r.get("char"): fm["character"] = f"[[{TITLE2NOTE.get(norm(r['char']), r['char'])}]]"
            if soul: rel.append(f"**Soul:** [[{soul}]]")
            if r.get("char"): rel.append(f"**Learned by (per wiki list):** {ctx['link'](r['char'], r['char'])}")
        elif r["group"] == "New Game Plus":
            if r["symbol"]:
                gnote = TITLE2NOTE.get(norm(r["symbol"]))
                rel.append(f"**Symbol shown beside the skill on the wiki list:** {ctx['link'](r['symbol'], r['symbol'])}")
                if gnote: fm["associated_god"] = f"[[{gnote}]]"
        for i, d in enumerate(r.get("dups", []), 2):
            for lab, key in (("Cost", "Cost"), ("Success rate", "Success Rate"), ("Unlock requirement", "Unlock Requirement")):
                v = d["cells"].get(key)
                if v is not None and clean(v, ctx, inline=True) not in ("", "-"):
                    rows.append(f"| **{lab} (listing {i})** | {clean(v, ctx, inline=True)} |")
        if r.get("dups"): rel.append(f"*The wiki lists this skill {len(r['dups']) + 1} times under this heading; each listing is shown.*")
        body = "\n\n".join(rel) + "\n\n| | |\n|---|---|\n" + "\n".join(rows)
        if r["target"] and norm(r["target"]) in PAGES:
            pass
        wurl = wiki_url(r["target"]) if r["target"] else wiki_url(r["list_title"], r["group"])
        body += f"\n\nWiki page: <{wurl}>"
        body += f"\n\n*Source: {cite(r['list_title'], r['note'])} ({r['group']})*"
        fm["sources"] = [f"[[{src_name(r['list_title'])}]]"]
        fm["retrieved"] = PAGES[r["list_title"]]["fetched"]
        fm["license"] = LICENSE
        add(folder, r["note"], fm, "\n".join(head) + body + footnotes(ctx), ctx)

    def add(folder, name, fm, body, ctx=None):
        NOTES[name] = dict(folder=folder, fm=fm, body=body)
        if ctx: targets_seen.update(ctx["targets"])

    for r in recs:
        if r["group"] in ("Contestant skills", "Soul skills", "God Affinity skills", "New Game Plus"):
            skill_note(r)

    # --- gods ---------------------------------------------------------------------------------
    gp = PAGES["The Gods"]; _, gsecs = sections(gp["wikitext"])
    gsec = {re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", t).replace("The ", "", 1) if t.startswith("The ") else t: txt for _, t, txt in gsecs}
    def god_section(name):
        for _, t, txt in gsecs:
            if t.strip().lower() in (name.lower(), "the " + name.lower()): return txt
        return None
    def info_rows(title, ctx):
        ib = infobox(PAGES[title]["wikitext"]) if title in PAGES else {}
        labels = [("aliases", "Aliases"), ("species", "Species / classification"), ("gender", "Gender"), ("god", "God"), ("soul", "Soul"),
                  ("birthDate", "Born"), ("birthPlace", "Birthplace"), ("deathDate", "Died"), ("age", "Age"), ("affiliation", "Affiliation"),
                  ("relatives", "Relatives")]
        rows = []
        for k, lab in labels:
            if ib.get(k, "").strip():
                raw_v = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", ib[k]) if k == "soul" else ib[k]
                v = clean(raw_v, ctx, inline=True)
                if k == "soul" and re.fullmatch(r"\w+ soul", v) and v in SOUL_NOTES: v = f"[[{v}]]"
                if v: rows.append(f"| **{lab}** | {v} |")
        return ("| | |\n|---|---|\n" + "\n".join(rows) + f"\n\n*Source: {cite(title, ctx['owner'])} (infobox)*") if rows else ""

    DOC_FOR = {"Gro-goroth": ["Skin Bible - Gro-goroth", "Studies of Gro-goroth I"], "Sylvian": ["Skin Bible - Sylvian", "Studies of Sylvian I"],
               "Vinushka": ["Skin Bible - Vinushka (unedited)"], "Rher": ["Skin Bible - Rher"], "Alll-mer": ["Skin Bible - Alll-mer"]}
    for t, cls in GODS.items():
        if t not in PAGES: continue
        nm = fname(t); ctx = make_ctx(nm)
        ib = infobox(PAGES[t]["wikitext"])
        first = "F&H2" if re.search(r"F&H2|Termina", PAGES[t]["wikitext"][:1500]) and not re.search(r"\[\[Fear & Hunger\]\]", PAGES[t]["wikitext"][:1500]) else "see page"
        fm = dict(type="god", classification=cls, aliases=[], tags=["god", cls.lower().replace(" ", "-")],
                  sources=[f"[[{src_name(t)}]]", f"[[{src_name('The Gods')}]]"], retrieved=PAGES[t]["fetched"], license=LICENSE)
        parts = [f"# {t}", "", f"**Classification (per wiki):** {cls}", ""]
        sec = god_section(t) or god_section(t.replace("Tormented One (F&H2)", "Tormented One"))
        if sec:
            parts.append("## Overview on *The Gods*\n\n" + clean(sec, ctx) + f"\n\n*Source: {cite('The Gods', nm)}*")
        ir = info_rows(t, ctx)
        if ir: parts.append("## Facts\n\n" + ir)
        parts.append("## Detailed page\n\n" + page_body(t, nm, ctx, base=2))
        gs = skill_by_god.get(t, [])
        if t == "God of the Depths": pass
        ngp = ngp_by_god.get(t, [])
        if gs or ngp:
            sk = ["## Skills granted by this god",
                  "*Skills below are the god-affinity skills the wiki lists under this god. The unlock requirement is the affinity level quoted by the wiki.*", ""]
            for g in ("F&H1", "F&H2"):
                lst = [r for r in gs if r["game"] == g]
                if lst:
                    sk.append(f"### {g}")
                    for r in lst:
                        reqs = [clean(x["cells"].get("Unlock Requirement", ""), ctx, inline=True) for x in [r] + r.get("dups", [])]
                        sk.append(f"- [[{r['note']}]] — {'; '.join(q for q in reqs if q) or 'requirement not listed'}")
                    sk.append("")
            if ngp:
                sk.append("### New Game Plus skills shown with this god's symbol (F&H2)")
                for r in ngp:
                    req = clean(r["cells"].get("Unlock Requirement", ""), ctx, inline=True)
                    sk.append(f"- [[{r['note']}]] — unlock: {req}")
            parts.append("\n".join(sk))
        for d in DOC_FOR.get(t, []):
            if d in PAGES: parts.append("")  # docs listed below
        docs = [d for d in DOC_FOR.get(t, []) if d in PAGES]
        if docs:
            parts.append("## In-game documents\n" + "\n".join(f"- [[{fname(d)}]]" for d in docs))
        pts = clean(f"", ctx)
        parts.append(f"## Sources\n- {cite(t, nm)}\n- {cite('The Gods', nm)}")
        fm["aliases"] = [a for a in {re.sub(r"\s+", " ", clean(x, ctx, inline=True)) for x in re.split(r"<br\s*/?>", ib.get("aliases", ""))} if a and len(a) < 60 and "[" not in a]
        add("Gods", nm, fm, "\n\n".join(parts) + footnotes(ctx), ctx)

    for t, (cls, nm) in SECTION_ONLY.items():
        ctx = make_ctx(nm); sec = god_section(t)
        if sec is None:
            sec = god_section(t.replace("Unnamed ", "Unnamed "))
        if sec is None: continue
        fm = dict(type="god", classification=cls, tags=["god", cls.lower().replace(" ", "-"), "minor-entity"], sources=[f"[[{src_name('The Gods')}]]"],
                  retrieved=gp["fetched"], license=LICENSE)
        body = f"# {nm}\n\n**Classification (per wiki):** {cls}\n\n> [!info] No standalone wiki page was fetched for this entity; everything below is from the *The Gods* page.\n\n" \
               + clean(sec, ctx) + f"\n\n*Source: {cite('The Gods', nm)}*"
        add("Gods", nm, fm, body + footnotes(ctx), ctx)

    # The Gods hub + Hall
    for t, nm in (("The Gods", "The Gods"), ("The Hall of the Gods", "The Hall of the Gods")):
        ctx = make_ctx(nm)
        fm = dict(type="hub", tags=["gods", "hub"], sources=[f"[[{src_name(t)}]]"], retrieved=PAGES[t]["fetched"], license=LICENSE)
        body = f"# {nm}\n\n"
        if t == "The Gods":
            body += "*Index of every god note in this vault, grouped by the wiki's classification. The long-form text of each entity is in its own note.*\n\n"
            by = defaultdict(list)
            for n, v in NOTES.items():
                if v["folder"] == "Gods": by[v["fm"].get("classification")].append(n)
            for cls in ("Old God", "Ascended God", "New God", "Blight", "Unspecified classification"):
                body += f"## {cls}s\n" + "\n".join(f"- [[{n}]]" for n in sorted(by.get(cls, []))) + "\n\n"
            lead, secs = sections(PAGES[t]["wikitext"])
            body += "## Trivia (from the wiki)\n\n" + clean(next((x for _, tt, x in secs if tt == "Trivia"), ""), ctx) + f"\n\n*Source: {cite(t, nm)}*\n"
            body += "\n## Skills granted by the gods\nSee [[Divine skills index]].\n"
        else:
            body += page_body(t, nm, ctx)
        add("Gods", nm, fm, body + footnotes(ctx), ctx)

    # --- souls ------------------------------------------------------------------------------------
    sp = PAGES["Soul type"]; swt = sp["wikitext"]
    months = {}
    for m in re.finditer(r"^\* '''(\w+)''' - (.*)$", swt, re.M):
        for s in re.findall(r"<font color=\"orange\">(.*?)</font>", m.group(2)):
            months[re.sub(r"\s*soul\s*$", "", s, flags=re.I).strip()] = m.group(1)
    known = {}  # soul name -> dict(holders titles, origin, quote)
    cur_origin = None
    for line in swt.split("\n"):
        h = re.match(r"^===\s*Introduced in (.*?)\s*===\s*$", line)
        if h: cur_origin = re.sub(r"[\[\]']", "", h.group(1)); continue
        if line.startswith("== "): cur_origin = cur_origin if line.startswith("== Known") else None
        m = re.match(r"^\* '''(\w+)'''(?: - (.*))?$", line)
        if m and cur_origin:
            known[m.group(1)] = dict(origin=cur_origin, holders_raw=m.group(2) or "", quote=None)
            last = m.group(1)
        q = re.match(r'^\*\* \'\'"(.*)"\'\'', line)
        if q and cur_origin and 'last' in locals() and last in known: known[last]["quote"] = q.group(1)
    ALT = {"Dominating": "Domination", "Enlightenment": "Enlightened"}
    for a, k in ALT.items():
        if a in months and k in known: months[k] = months[a]
    soul_names = list(known)
    # gods linked by soul via infobox
    god_by_soul = defaultdict(list)
    for t in list(GODS) + []:
        if t in PAGES:
            ib = infobox(PAGES[t]["wikitext"]); s = re.sub(r"<[^>]+>|\[\[|\]\]", "", ib.get("soul", "")).strip()
            sm = re.match(r"(\w+) soul", s)
            if sm: god_by_soul[sm.group(1)].append(t)
    for sname in soul_names:
        nm = f"{sname} soul"; ctx = make_ctx(nm); k = known[sname]
        fm = dict(type="soul", soul_type=sname, birth_month=months.get(sname), origin=k["origin"], aliases=[sname],
                  tags=["soul"], sources=[f"[[{src_name('Soul type')}]]", f"[[{src_name('Skills List F&H2')}]]"], retrieved=sp["fetched"], license=LICENSE)
        parts = [f"# {nm}", ""]
        rows = ["| | |", "|---|---|", f"| **Birth month (wiki chart)** | {months.get(sname, 'not listed')} |",
                f"| **Introduced in** | {clean(k['origin'], ctx, inline=True)} (per wiki's *Soul type* page) |"]
        if sname in ALT.values(): rows.append(f"| **Chart name** | listed as \"{[a for a,b in ALT.items() if b==sname][0]}\" in the month chart; same soul by the wiki's count of 28 |")
        parts.append("\n".join(rows))
        parts.append(f"*Source: {cite('Soul type', nm)}*")
        parts.append("## Definition")
        if k["quote"]:
            parts.append(f"> {k['quote']}\n\n*In-game description as quoted on the wiki. Source: {cite('Soul type', nm)}*")
        else:
            parts.append("> [!question] Unverified\n> The wiki's *Soul type* page records no in-game description text for this soul. Add it from the game files when available.")
        holders = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", k["holders_raw"])
        parts.append("## Characters with this soul")
        if holders:
            parts.append("\n".join(f"- {ctx['link'](h, h)}" for h in holders) + f"\n\n*Source: {cite('Soul type', nm)}*")
        else:
            parts.append("*No holder is recorded on the wiki's Soul type page.*")
        gb = god_by_soul.get(sname, [])
        if gb:
            parts.append("## Gods named after / bearing this soul\n" + "\n".join(f"- {ctx['link'](g, g)}" for g in gb) + "\n\n*Per the infobox `soul` field on each god's page.*")
        sk = skill_by_soul.get(sname, [])
        parts.append("## Skills tied to this soul")
        if sk:
            for g in ("F&H1", "F&H2"):
                lst = [r for r in sk if r["game"] == g]
                if lst:
                    who = sorted({r["char"] for r in lst if r.get("char")})
                    parts.append(f"### {g}" + (f" — table for {', '.join(ctx['link'](w, w) for w in who)}" if who else ""))
                    parts.append("\n".join(f"- [[{r['note']}]]" for r in lst))
            parts.append(f"\n*Source: {cite('Skills List F&H2', nm)} / {cite('Skills List F&H1', nm)}*")
        else:
            parts.append("*The wiki's skill lists have no skill table for this soul.*")
        parts.append(f"## Sources\n- {cite('Soul type', nm)}\n- {cite('Skills List F&H2', nm)}")
        add("Souls", nm, fm, "\n\n".join(parts) + footnotes(ctx), ctx)
    # months not known individually (months chart only) -> create stubs for any chart souls missing
    for sname, mon in months.items():
        if sname in known or sname in ALT: continue
        nm = f"{sname} soul"
        if nm in NOTES: continue
        ctx = make_ctx(nm)
        fm = dict(type="soul", soul_type=sname, birth_month=mon, origin="month chart only", aliases=[sname], tags=["soul"],
                  sources=[f"[[{src_name('Soul type')}]]"], retrieved=sp["fetched"], license=LICENSE)
        add("Souls", nm, fm, f"# {nm}\n\nBirth month (wiki chart): {mon}\n\n> [!question] Unverified\n> Appears only in the wiki's month chart.\n\n*Source: {cite('Soul type', nm)}*", ctx)
    # soul overview
    ctx = make_ctx("Soul types")
    ov = [f"# Soul types", "", f"*{len(NOTES_SOULS(NOTES))} soul-type notes. Source page flagged by the wiki: some content comes from supplementary sources and is subject to change.*", ""]
    ov.append(page_body("Soul type", "Soul types", ctx, only={"Overview", "Skills and inheritance", "Soul types and New Gods"}))
    ov.append("## All souls\n" + "\n".join(f"- [[{n}]]" + (f" — {v['fm'].get('birth_month')}" if v["fm"].get("birth_month") else "") for n, v in sorted(NOTES.items()) if v["folder"] == "Souls"))
    add("Souls", "Soul types", dict(type="hub", tags=["soul", "hub"], sources=[f"[[{src_name('Soul type')}]]"], retrieved=sp["fetched"], license=LICENSE),
        "\n\n".join(ov) + footnotes(ctx), ctx)

    # --- characters ---------------------------------------------------------------------------------
    for t in CHARS:
        if t not in PAGES: continue
        nm = fname(t); ctx = make_ctx(nm); ib = infobox(PAGES[t]["wikitext"])
        sm = re.search(r"(\w+) soul", re.sub(r"<[^>]+>", "", ib.get("soul", "")))
        fm = dict(type="character", soul=f"[[{sm.group(1)} soul]]" if sm and f"{sm.group(1)} soul" in SOUL_NOTES else None,
                  game=["F&H1"] if t in ("Cahara", "D'arce", "Ragnvaldr", "Enki") else ["F&H2"], aliases=[], tags=["character"],
                  sources=[f"[[{src_name(t)}]]"], retrieved=PAGES[t]["fetched"], license=LICENSE)
        parts = [f"# {t}", ""]
        if sm: parts.append(f"**Soul:** " + (f"[[{sm.group(1)} soul]]" if (sm.group(1) + ' soul') in SOUL_NOTES else sm.group(1) + ' soul') + "\n")
        parts.append("## Facts\n\n" + info_rows(t, ctx))
        parts.append("## Biography\n\n" + page_body(t, nm, ctx, base=2))
        ch = skill_by_char.get(t, [])
        if ch:
            parts.append("## Contestant / soul skills\n" + "\n".join(f"- [[{r['note']}]] ({r['game']})" for r in ch) + f"\n\n*Source: {cite('Skills List F&H2' if ch[0]['game']=='F&H2' else 'Skills List F&H1', nm)}*")
        parts.append(f"## Sources\n- {cite(t, nm)}")
        fm["aliases"] = [a for a in {re.sub(r"\s+", " ", clean(x, ctx, inline=True)) for x in re.split(r"<br\s*/?>", ib.get("aliases", ""))} if a and len(a) < 60 and "[" not in a]
        add("Characters", nm, fm, "\n\n".join(parts) + footnotes(ctx), ctx)

    # --- lore docs + mechanics ----------------------------------------------------------------------
    for t in DOCS + MECH:
        if t not in PAGES: continue
        nm = fname(t); ctx = make_ctx(nm)
        folder = "Lore" if t in DOCS else "Mechanics"
        fm = dict(type="document" if t in DOCS else "mechanic", tags=[folder.lower()], sources=[f"[[{src_name(t)}]]"], retrieved=PAGES[t]["fetched"], license=LICENSE)
        body = f"# {t}\n\n" + page_body(t, nm, ctx, base=2) + f"\n\n## Sources\n- {cite(t, nm)}"
        add(folder, nm, fm, body + footnotes(ctx), ctx)

    # --- hubs --------------------------------------------------------------------------------------------
    def idx(folder, label):
        return f"## {label}\n" + "\n".join(f"- [[{n}]]" for n, v in sorted(NOTES.items()) if v["folder"] == folder and v["fm"].get("type") != "hub") + "\n"
    for name, title in GAMES.items():
        if title in {"Fear & Hunger", "Fear & Hunger 2 Termina"}:
            pass
    div = ["# Divine skills index", "", "*Skills the wiki lists as god-affinity skills, grouped by god.*", ""]
    for g in sorted(set(r["god"] for r in recs if r["group"] == "God Affinity skills")):
        div.append(f"## {g}")
        for gm in ("F&H1", "F&H2"):
            lst = [r for r in recs if r["group"] == "God Affinity skills" and r["god"] == g and r["game"] == gm]
            if lst: div.append(f"**{gm}:** " + ", ".join(f"[[{r['note']}]]" for r in lst))
        div.append("")
    add("Skills", "Divine skills index", dict(type="hub", tags=["skill", "hub"], sources=[f"[[{src_name('Skills List F&H2')}]]"]), "\n".join(div))
    soulsk = ["# Soul skills index", ""]
    for s in sorted(skill_by_soul, key=lambda x: x or ""):
        if s: soulsk.append(f"- [[{s} soul]]: " + ", ".join(f"[[{r['note']}]]" for r in skill_by_soul[s]))
    add("Skills", "Soul skills index", dict(type="hub", tags=["skill", "hub"]), "\n".join(soulsk))
    root = ["# Fear & Hunger Research — Index", "",
            "Vault documenting *Fear & Hunger* and *Fear & Hunger 2: Termina*. Content is from https://fearandhunger.wiki.gg (" + LICENSE + "); see [[About this vault]].", "",
            "- [[The Gods]] · [[The Hall of the Gods]]", "- [[Divine skills index]] · [[Soul skills index]]", "- [[Soul types]]", "",
            idx("Gods", "Gods"), idx("Souls", "Souls"), idx("Characters", "Characters"), idx("Lore", "In-game documents"), idx("Mechanics", "Mechanics")]
    add("", "00 Index", dict(type="hub", tags=["index"]), "\n".join(root))
    add("", "About this vault", dict(type="hub", tags=["meta"]),
        "# About this vault\n\n- Scope so far: gods, god-granted skills, soul types with their skills and characters.\n- Facts come from the wiki pages cited on each note (revision id and date on the `Wiki - …` source notes). Wiki text is licensed " + LICENSE + "; notes reuse it with attribution to the wiki's contributors.\n- The wiki marks parts of its content as coming from supplementary sources (e.g. developer social posts) and not from the game; where the wiki says so it is preserved.\n- Game-file facts are **not** included yet; they will be added and labelled `(game files)`.\n- `[!question] Unverified` callouts mark gaps. Nothing is filled from memory.\n- Skills not covered yet: General skills and Unused skills lists.\n- Rebuild: `scripts/fetch_wiki.py` then `scripts/build_vault.py`.\n")

    # --- game hubs
    for title, nm in GAMES.items():
        if title in PAGES:
            ctx = make_ctx(nm)
            fm = dict(type="hub", tags=["game"], sources=[f"[[{src_name(title)}]]"], retrieved=PAGES[title]["fetched"], license=LICENSE)
            gname = "F&H1" if nm == "Fear & Hunger" else "F&H2"
            sk = [f"- [[{r['note']}]]" for r in recs if r["game"] == gname and r["group"] in ("God Affinity skills",)]
            add("Games", nm, fm, f"# {title}\n\nWiki page: <{wiki_url(title)}>\n\n## God-affinity skills in this game\n" + "\n".join(sk) + f"\n\n*Source: {cite(title, nm)}*")

    # --- Hexen skill table: one standalone page, deliberately NO wikilinks (keeps the graph view uncluttered) ---
    def hexen_table():
        pctx = {"fn": [], "refs": {}, "n": 0, "owner": "Hexen skill table", "targets": set(), "link": lambda t, d, f="": d}
        GOD_SYM = {"All-mer": "Alll-mer", "Fear and Hunger": "God of Fear and Hunger"}
        char2soul = {}
        for r in recs:
            if r["group"] in ("Contestant skills", "Soul skills") and r.get("char") and r.get("soul"):
                char2soul[r["char"]] = r["soul"]
        KNOWN_GODS = {r["god"] for r in recs if r["group"] == "God Affinity skills"}
        extras = []
        for gm, page in (("F&H1", "Skills List F&H1"), ("F&H2", "Skills List F&H2")):
            extras += skill_records(gm, page, groups={"General skills", "Unused skills"})

        def get(r, *keys):
            low = {k.lower(): v for k, v in r["cells"].items()}
            for k in keys:
                if k.lower() in low: return low[k.lower()]
            return None
        def cell(r, *keys):
            v = get(r, *keys)
            if v is None: return ""
            out = clean(v, pctx, inline=True)
            out = re.sub(r"\[\^\d+\]", "", out)
            out = re.sub(r"^/\s*", "", out)  # symbol images in the name cell leave a leading <br>
            return "" if out == "-" else out.replace("|", "\\|").replace("\n", " ")

        def classify(r):
            """-> (kind, key, character). Soul/character first, then god, per the wiki's own table text only."""
            unlock_raw = re.sub(r"<[^>]+>", "", get(r, "Unlock Requirement", "Unlock method", "Unlock Method") or "")
            unlock_raw = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", unlock_raw)
            m = re.search(r"([A-Z][\w'’-]+)?\s*\((\w+) soul\)", unlock_raw)
            if m: return "soul", m.group(2), m.group(1)
            for ch in sorted(char2soul, key=len, reverse=True):
                if re.search(r"\b" + re.escape(ch) + r"\b", unlock_raw):
                    return "soul", char2soul[ch], ch
            if r.get("char"):
                return ("soul", r["soul"], r["char"]) if r.get("soul") else ("char", r["char"], r["char"])
            if r.get("symbol"): return "god", GOD_SYM.get(r["symbol"], r["symbol"]), None
            if r.get("god"): return "god", r["god"], None
            ma = re.search(r"([A-Z][\w'’ -]+?) affinity", unlock_raw)
            if ma:
                g = GOD_SYM.get(ma.group(1).strip(), ma.group(1).strip())
                if g in KNOWN_GODS or g in ("Logic",): return "god", g, None
            return "none", None, None

        allrows = [r for r in recs if r["group"] in ("Contestant skills", "Soul skills", "God Affinity skills", "New Game Plus")] + extras
        placed = defaultdict(list)   # (kind, key) -> rows
        for r in allrows:
            kind, key, ch = classify(r)
            r["_char"] = ch or r.get("char") or ""
            placed[(kind, key)].append(r)

        def one(r, dup=False):
            name = cell(r, "Name") or r["name"]
            if dup: name += " (second listing)"
            return "| " + " | ".join([name, r["game"], r["group"], r["_char"], cell(r, "Description"), cell(r, "Effect"), cell(r, "Cost"),
                                       cell(r, "Success Rate", "Success rate"), cell(r, "Unlock Requirement", "Unlock method", "Unlock Method")]) + " |"
        def rows_for(lst):
            order = {"Contestant skills": 0, "Soul skills": 0, "God Affinity skills": 0, "New Game Plus": 1, "General skills": 2, "Unused skills": 3}
            out = []
            for r in sorted(lst, key=lambda r: (r["game"], order.get(r["group"], 9))):
                out.append(one(r))
                for d in r.get("dups", []): d["_char"] = r["_char"]
                out += [one(d, True) for d in r.get("dups", [])]
            return out
        def nrows(lst): return sum(1 + len(x.get("dups", [])) for x in lst)
        def counts(lst): return ", ".join(f"{g}: {nrows([x for x in lst if x['game'] == g])}" for g in ("F&H1", "F&H2") if any(x["game"] == g for x in lst))
        HDR = "| Skill | Game | Wiki list | Character | Description | Effect | Cost | Success rate | Unlock requirement / method |\n|---|---|---|---|---|---|---|---|---|"
        def anchor(h): return "#" + urllib.parse.quote(h, safe="")

        souls = sorted(k for (kd, k) in placed if kd == "soul")
        chars = sorted(k for (kd, k) in placed if kd == "char")
        gods = sorted(k for (kd, k) in placed if kd == "god")
        none = placed.get(("none", None), [])
        out = ["# Hexen skill table", "",
               "*Every skill on the wiki's skill lists for Fear & Hunger (F&H1) and Fear & Hunger 2: Termina (F&H2): contestant/soul skills, god-affinity skills, New Game Plus, General and Unused skills. "
               "Sorted by soul first (by character where the character has no soul listed), then by god. Skills with neither are at the end. Standalone page: no wikilinks, nothing links here.*", "",
               "*How rows were placed (only from the wiki's own table text): a soul or character named in the unlock column, or the table the skill sits in, decides the soul; otherwise a god symbol beside the skill or an \"X affinity\" requirement decides the god. Effect text is never used to guess. The \"Wiki list\" column says which list the row came from.*", "",
               "## Index", "", "**Souls**", ""]
        for s_ in souls: out.append(f"- [{s_} soul]({anchor('Soul ' + s_)}) — {counts(placed[('soul', s_)])}")
        if chars:
            out += ["", "**Characters with no soul listed**", ""]
            for c_ in chars: out.append(f"- [{c_}]({anchor('Character ' + c_)}) — {counts(placed[('char', c_)])}")
        out += ["", "**Gods**", ""]
        for g_ in gods: out.append(f"- [{g_}]({anchor('God ' + g_)}) — {counts(placed[('god', g_)])}")
        out += ["", f"**No soul or god listed**: [General and unattributed skills]({anchor('No soul or god listed')}) — {counts(none)}", "",
                "## A-Z skill index", "", "| Skill | Game | Wiki list | Placed under |", "|---|---|---|---|"]
        az = set()
        for (kd, k), lst in placed.items():
            lab = {"soul": f"Soul {k}", "char": f"Character {k}", "god": f"God {k}"}[kd] if kd != "none" else "No soul or god listed"
            for r in lst: az.add((cell(r, "Name") or r["name"], r["game"], r["group"], lab))
        for a in sorted(az, key=lambda x: (x[0].lower(), x[1], x[2], x[3])): out.append("| " + " | ".join(a) + " |")
        out += ["", "# Skills by soul", ""]
        for s_ in souls: out += [f"## Soul {s_}", "", HDR] + rows_for(placed[("soul", s_)]) + [""]
        if chars:
            out += ["# Skills by character (no soul listed)", ""]
            for c_ in chars: out += [f"## Character {c_}", "", HDR] + rows_for(placed[("char", c_)]) + [""]
        out += ["# Skills by god", ""]
        for g_ in gods: out += [f"## God {g_}", "", HDR] + rows_for(placed[("god", g_)]) + [""]
        out += ["# No soul or god listed", "", f"## No soul or god listed", "", HDR] + rows_for(none) + [""]
        notes_ = ["Marina is listed under \"Enlightened soul (Demo)\" in the wiki's Unused skills list while her contestant skill table says Changeling soul; the row is shown as the wiki gives it."]
        ps = [PAGES["Skills List F&H1"], PAGES["Skills List F&H2"]]
        out += ["---", "", "**Notes:** " + " ".join(notes_), "", "**Sources:** " + "; ".join(f"[{p['title']}]({p['url']}) (revision {p['revid']}, {p['timestamp'][:10]}, fetched {p['fetched']})" for p in ps)
                + ". Text © Fear & Hunger Wiki contributors, " + LICENSE + ".", ""]
        fm = dict(type="hexen-table", tags=["skill", "hexen", "table"], sources=["Fear & Hunger Wiki: Skills List F&H1", "Fear & Hunger Wiki: Skills List F&H2"],
                  retrieved=max(p["fetched"] for p in ps), license=LICENSE, graph_note="no wikilinks by design", row_count=sum(nrows(v) for v in placed.values()))
        NOTES["Hexen skill table"] = dict(folder="Hexen", fm=fm, body="\n".join(out))
    hexen_table()

    # --- source notes
    for sname, users in SRC_USED.items():
        title = next((t for t in PAGES if src_name(t) == sname), None)
        if not title: continue
        p = PAGES[title]
        body = f"# {sname}\n\n- Wiki page: <{p['url']}>\n- Revision id: {p['revid']}\n- Revision timestamp: {p['timestamp']}\n- Retrieved via MediaWiki API (see `scripts/fetch_wiki.py`)\n- License: {LICENSE}\n- Publisher: Fear & Hunger Wiki (fearandhunger.wiki.gg), contributors credited in the page history\n\n## Cited by\n" + "\n".join(f"- [[{u}]]" for u in sorted(users) if u in NOTES or True)
        NOTES[sname] = dict(folder="Sources", fm=dict(type="source", publisher="fearandhunger.wiki.gg", url=p["url"], revid=p["revid"], revision_timestamp=p["timestamp"], retrieved=p["fetched"], license=LICENSE), body=body)
    return targets_seen

def NOTES_SOULS(n): return [k for k, v in n.items() if v["folder"] == "Souls" and v["fm"].get("type") == "soul"]

def resolve_redirects(targets):
    todo = sorted(t for t in targets if t and t not in TITLE2NOTE)
    red = {}
    for i in range(0, len(todo), 40):
        chunk = todo[i:i + 40]
        url = API + "?" + urllib.parse.urlencode(dict(action="query", titles="|".join(chunk), redirects=1, format="json", formatversion=2))
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "fh-vault-research/1.0"}), timeout=60))
        except Exception as e:
            print("redirect lookup failed", e); break
        for r in d.get("query", {}).get("redirects", []):
            red[r["from"]] = r["to"]
    (RAW / "_redirects.json").write_text(json.dumps(red, ensure_ascii=False, indent=1), encoding="utf-8")

def write(final_dir):
    import shutil
    for d in ("Gods", "Skills", "Souls", "Characters", "Lore", "Mechanics", "Games", "Sources", "Hexen"):
        p = final_dir / d
        if p.exists(): shutil.rmtree(p)
    for r in final_dir.glob("*.md"):
        if r.name not in ("README.md",): r.unlink()
    for name, n in NOTES.items():
        folder = final_dir / n["folder"]; folder.mkdir(parents=True, exist_ok=True)
        fm = {k: v for k, v in n["fm"].items() if v not in (None, [], "")}
        (folder / f"{name}.md").write_text(frontmatter(fm) + "\n\n" + n["body"].strip() + "\n", encoding="utf-8")

if __name__ == "__main__":
    t1 = build(final=False)
    resolve_redirects(t1)
    build(final=True)
    write(VAULT)
    print(len(NOTES), "notes written")
    print("templates seen:", dict(sorted(TEMPLATES_SEEN.items(), key=lambda x: -x[1])[:25]))
