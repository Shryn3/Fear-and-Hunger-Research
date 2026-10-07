# Fear & Hunger Research

Obsidian vault documenting **Fear & Hunger** (F&H1) and **Fear & Hunger 2: Termina** (F&H2).
Open this folder as a vault in Obsidian and start at **`00 Index`**.

## Covered so far
| Area | Folder | Notes |
|---|---|---|
| Gods (Old, Ascended, New, other entities, Blights) | `Gods/` | 33 incl. hubs `The Gods`, `The Hall of the Gods` |
| God-granted skills (god-affinity), both games | `Skills/Divine/` | 46 |
| Soul types (28) with definitions, holders and skills | `Souls/` | 29 incl. `Soul types` overview |
| Soul-tied skills (contestant / soul skills), both games | `Skills/Soul/` | 70 |
| New Game Plus skills (with the god symbol shown beside them) | `Skills/New Game Plus/` | 5 |
| Soul-holding characters | `Characters/` | 19 |
| In-game documents about the gods (Skin Bibles etc.) | `Lore/` | 8 |
| Mechanics (Hexen, Soul stone, Rev, ritual circles…) | `Mechanics/` | 6 |
| One note per cited wiki page, with revision id | `Sources/` | 65 |
| **Hexen skill table**: every god/soul skill, both games, one standalone page (no wikilinks by design, so it adds nothing to the graph) | `Hexen/Hexen skill table.md` | 1 |

**Not yet covered:** General skills and Unused skills lists; non-soul characters; locations, factions, items, enemies; game-file data.

## Conventions
- **Links:** Obsidian wikilinks; a note's filename is its title. God <-> skill, soul <-> character <-> skill are linked both ways. Wiki pages that have no note yet are linked to the wiki as normal markdown links.
- **Citations:** every block ends with `*Source: [[Wiki - …]]*`; the source note has the wiki URL, revision id, revision timestamp, retrieval date and license. The wiki's own footnotes are kept as `[^n]: Wiki citation: …`.
- **Provenance:** the wiki says some content comes from supplementary sources (e.g. developer social posts). Where it says so, the notes keep that wording. `[!warning]` callouts mark text the wiki flags as speculation; `[!question] Unverified` marks gaps. Nothing is filled from memory.
- **Game files:** not added yet; when added they are labelled `(game files)` and kept apart from wiki facts.
- **License:** wiki text is **CC BY-SA 4.0** (https://creativecommons.org/licenses/by-sa/4.0/). Notes reuse it with attribution to the wiki's contributors. If this repo is ever made public, keep the attribution and share-alike.

## Rebuilding
```
python3 scripts/fetch_wiki.py raw < scripts/titles.txt   # needs fearandhunger.wiki.gg reachable
python3 scripts/build_vault.py raw .                     # regenerates the notes (overwrites Gods/ Skills/ Souls/ … )
python3 scripts/check_links.py                            # reports broken [[wikilinks]]
```
`raw/` is not committed. Generated folders are overwritten on rebuild, so put hand-written additions in new notes, not in generated ones.
