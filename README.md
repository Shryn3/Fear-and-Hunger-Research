# Fear & Hunger Research

A research document on **Fear & Hunger** (F&H1) and **Fear & Hunger 2: Termina** (F&H2), written as an Obsidian vault.
Download the repository (Code → Download ZIP, or clone it), unzip it, and open the folder as a vault in Obsidian. Start at **`00 Index`**.
It is plain Markdown, so it also reads fine in any editor and moves between machines as ordinary files.

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
| One note per cited wiki page, with revision id (main wiki `Wiki - …`, Tormentpedia `Tormentpedia - …`) | `Sources/` | 65 + 44 |
| Pictures: infobox portraits and sprites, god symbols, soul icons, book images, and images from the wiki's text (257 files, 43 MB), embedded in the notes under an "Images" heading | `Images/` | 257 |
| **Unofficial research** (theories about gods the game and wiki do not describe, e.g. Amon, the Star God). **Kept completely apart: nothing links in or out, and everything is tagged by kind** | `Unofficial/` | 6 |
| **Hexen skill table**: all 165 skill listings from both games' wiki lists (soul/god skills, New Game Plus, General, Unused), sorted by soul or character, then god. One standalone page with no wikilinks by design, so it adds nothing to the graph view | `Hexen/Hexen skill table.md` | 1 |

**Compared with the Tormentpedia so far:** skills, gods, soul-holding characters, the Skin Bibles and Studies documents, and the Hexen F&H1, Ritual Circles and Marriage of Flesh mechanics notes. Not compared: souls (its soul pages are empty stubs) and mechanics without a counterpart there (Rev, Soul stone, God manifesto have no Tormentpedia page; its "The Hexen" page, for F&H2, has no matching note). **Images not included:** gallery sprites and screenshots, enemy and location images, and images inside skill tables. **Not yet covered at all:** non-soul characters; locations, factions, items, enemies; game-file data. The gameplay and dialogue sections of god and character pages are not reproduced (see [[Verification]]).

## Accuracy
The notes were checked against their sources with an independent reader; results, the problems found and fixed, and what is left out are in [[Verification]].

## Unofficial section
Theories and community speculation live only in `Unofficial/`. Notes there are prefixed "Unofficial - ", carry an UNOFFICIAL banner, and tag every statement as [WIKI-REPORTED], [THEORY] or [UNREAD]. No note in that folder links to an official note and no official note links into it; `_tools/check_links.py` enforces this. What could and could not be retrieved is in `Unofficial/Unofficial - Source log.md`.

## Conventions
- **Links:** Obsidian wikilinks; a note's filename is its title. God ↔ skill and soul ↔ character ↔ skill are linked both ways. Wiki pages that have no note yet are linked to the wiki as normal markdown links.
- **Citations:** every block ends with `*Source: [[Wiki - …]]*`; the source note gives the wiki URL, revision id, revision timestamp, retrieval date and license. The wiki's own footnotes are kept as `[^n]: Wiki citation: …`.
- **Provenance:** the wiki says some content comes from supplementary sources (e.g. developer social posts). Where it says so, the notes keep that wording. `[!warning]` callouts mark text the wiki flags as speculation; `[!question] Unverified` marks gaps. Nothing is filled in from memory.
- **Other wikis:** the main wiki (fearandhunger.wiki.gg) is the baseline. A second, separate community wiki, *Fear and Hunger: the Tormentpedia* (fearandhunger.fandom.com), is used as a supplementary source. It is cited only where it adds something or says something different, always in a section headed **Other wikis** (skill and god notes) or **Other wikis: Tormentpedia** (Hexen skill table), with its own `Tormentpedia - …` source note. Its text is quoted as written and not reconciled with the main wiki.
- **Images:** every picture is embedded with the wiki's own caption and a link to its wiki File page. The artwork is the game creator's, not covered by the wiki's text license; the vault is private and `Images/Image catalogue.md` lists each file, its uploader and its checksum. Remove `Images/` before sharing the vault publicly.
- **Game files:** not added yet. When added they are labelled `(game files)` and kept apart from wiki facts.
- **Editing:** the notes are the document. Edit and extend them directly and keep the citation on whatever you add.
- **License:** wiki text is **CC BY-SA 4.0** (https://creativecommons.org/licenses/by-sa/4.0/). The notes reuse it with attribution to the wiki's contributors. If this is ever shared publicly, keep the attribution and share-alike.

## Optional
`_tools/check_links.py` lists `[[wikilinks]]` that point to a note that does not exist (`python3 _tools/check_links.py`). The vault does not need it.
