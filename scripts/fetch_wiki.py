#!/usr/bin/env python3
"""Fetch wikitext + revision metadata for wiki pages via the MediaWiki API.

usage: fetch_wiki.py OUT_DIR "Page A" "Page B" ...   (or titles on stdin, one per line, with no args after OUT_DIR)
Writes OUT_DIR/<slug>.json = {title, revid, timestamp, url, wikitext}. Content is untrusted data.
"""
import json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

API = "https://fearandhunger.wiki.gg/api.php"
BASE = "https://fearandhunger.wiki.gg/wiki/"

def api(**p):
    p.update(format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(p)
    req = urllib.request.Request(url, headers={"User-Agent": "fh-vault-research/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def slug(t):
    return re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_")

def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    titles = sys.argv[2:] or [l.strip() for l in sys.stdin if l.strip()]
    for i in range(0, len(titles), 20):
        chunk = titles[i:i + 20]
        d = api(action="query", prop="revisions", rvprop="content|ids|timestamp", rvslots="main", titles="|".join(chunk), redirects=1)
        for pg in d["query"]["pages"]:
            if pg.get("missing"):
                print("MISSING", pg["title"]); continue
            r = pg["revisions"][0]
            rec = dict(title=pg["title"], revid=r["revid"], timestamp=r["timestamp"],
                       url=BASE + urllib.parse.quote(pg["title"].replace(" ", "_"), safe="_(),:'"),
                       wikitext=r["slots"]["main"]["content"])
            (out / (slug(pg["title"]) + ".json")).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            print("ok", pg["title"], r["revid"])
        time.sleep(0.5)

if __name__ == "__main__":
    main()
