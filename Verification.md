---
type: "meta"
tags: ["meta", "verification"]
checked: "2026-10-07"
---

# Verification

How the notes were checked against their sources, what was found, and what is deliberately left out. Checked 2026-10-07 against the wiki revisions named in the `Sources/` notes.

## Method
The notes were first built from the wiki's page text. They were then checked with a **second, independently written reader** (a different wikitext parser and different table and link code), comparing words, numbers and word order cell by cell and section by section. Any mismatch was read by hand against the raw wikitext. No game files were used.

## Results
| Check | Compared | Result |
|---|---|---|
| Hexen skill table: every cell (description, effect, cost, success rate, unlock) vs the wiki's skill tables | 165 rows | identical text and order; the only difference is that numbered lists carry running numbers |
| Hexen skill table: soul / character / god placement vs the wiki's headings, god symbols and unlock text | 165 rows | all placed as the wiki states |
| Soul notes: birth month, game introduced, holders, in-game quote vs the Soul type page | 28 souls | all correct; holders now use the wiki's own link text |
| Citations: the wiki's own footnotes vs the notes' footnotes | 111 | identical text |
| Infobox facts (born, age, species, soul, relatives, …) vs each note's Facts table | 255 | all correct; 5 checker flags, all explained (4 were citation text counted twice, 1 is an unclosed tag in the wiki's own source) |
| Prose sections of gods, characters, documents and mechanics vs the wiki's sections | every included section | no content differences after the fixes below |
| Links to the wiki | 408 distinct pages | 15 links had a stray backslash typo in the wiki's source and now resolve; 5 pages the wiki links to do not exist there and are shown as plain text |
| Images: each file vs the SHA-1 checksum the wiki's API gives for it | 257 files | all match (the wiki's image CDN can serve a recompressed copy; these are the originals) |
| Image embeds in notes vs files in `Images/` | 388 embeds | all resolve |
| Unofficial section: every quoted passage vs the stored page text and revision | 13 quotes, 4 pages | all word for word; the X post is quoted from a search-result title only and is marked as such |
| Tormentpedia material (see [[About this vault]]): every quoted statement, pair and table value vs its Tormentpedia page, and the main-wiki side vs these notes | 873 items | all word for word |

## Problems found and fixed
1. Image captions had been dropped (some carry lore, e.g. the museum clock's sigil list). They are now kept as "Image caption: …".
2. *The Gods* hub was missing the class introductions, the Fellowship story, the Blights and Other-entities sections; *The Hall of the Gods* and the Mechanics pages were missing sections my gameplay filter had removed (Soul stone locations, ritual-circle locations, Hexen table locations).
3. Heading text like "41px Perfection Circle" (an image size leaking into a heading).
4. Marina's relatives row contained a garbled neighbouring field; phobias were not shown at all. Phobias now appear in Facts.
5. Links with a stray backslash, links to pages that do not exist, and aliases I had invented ("The Girl" and "Girl" were pointed at the God of Fear and Hunger note; the wiki treats them as a separate page).
6. Soul holder lists showed page names instead of the wiki's link text ("Ronn Chambara", "The Mourning One").
7. One Tormentpedia block quoted a mangled table fragment as a "statement".

## What is deliberately not reproduced
For gods and characters the notes include the wiki's lead, lore, history, personality, trivia and similar sections, but **not** the gameplay and dialogue sections: Location / Recruitment, Battle, Strategy, Fear & Hunger Mode and Masoχ-S/M Mode, Dialogue(s), Interactions, Special interactions, Item drops, Gallery, Navigation and References. Each note's source note links the full wiki page. The Tormentpedia comparison covers the same sections.

## Images and the Unofficial section
- Pictures were taken only from the wiki's File pages. Gallery sprites, screenshots and enemy or location art were left out.
- Reddit, X, YouTube transcripts and Steam threads could not be read from the cloud environment, so the Unofficial section is thin; its source log says exactly what was tried. Search-tool summaries were not used as evidence because one of them misattributed a claim to the Skin Bible.

## Limits
- The wiki itself is a community source. Some of its text comes from supplementary sources (developer posts); notes keep the wiki's wording about that, and the wiki's "speculation" flags show as warnings.
- Accuracy here means "the same as the wiki at the stated revision". It is not a check against the game; game-file facts are not yet included.
- Where the Tormentpedia disagrees with the main wiki, both are quoted and neither is declared correct.
