# Fear & Hunger Research

Obsidian vault documenting **Fear & Hunger** (F&H1) and **Fear & Hunger 2: Termina** (F&H2).
Open this folder as a vault in Obsidian.

## Structure
| Folder | Contents |
|---|---|
| `Gods/` | One note per god: nature, lore, worship, related characters |
| `Skills/` | One note per skill. `Skills/Divine/` holds skills granted by gods |
| `Souls/` | One note per soul: abilities, definition, linked character |
| `Characters/` | One note per character |
| `Sources/` | One note per cited source (wiki page or game file) |
| `_templates/` | Note templates (God, Skill, Soul, Character, Source) |
| `scripts/` | `check_links.py` — reports broken `[[wikilinks]]` |

## Conventions
- **Links:** Obsidian wikilinks, note filename = page title, e.g. `[[Example Note]]`. Link every god, skill, soul and character the first time it appears in a note.
- **Two-way links:** a god lists its skills; each skill links back to its god. A soul links to its character and its abilities.
- **Frontmatter:** every note has `type`, `game` (`F&H1`, `F&H2` or `both`), `sources` (list of `[[Sources/...]]` links) and `retrieved`.
- **Citations:** each fact comes from an official source and is cited as a footnote `[^1]` pointing at a `Sources/` note.
  Wiki = https://fearandhunger.wiki.gg ; game-file facts are labelled `(game files)` and kept apart from wiki facts.
- **Uncertainty:** never fill gaps from memory. Mark unknowns `> [!question] Unverified` with what is missing.

## Checking links
`python3 scripts/check_links.py` lists wikilinks that point to notes which do not exist.
