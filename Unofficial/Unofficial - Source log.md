---
type: "unofficial"
status: "unofficial"
retrieved: "2026-10-07"
tags: ["unofficial"]
cssclasses: ["fh-vault", "fh-unofficial"]
---

> [!danger] UNOFFICIAL RESEARCH
> This section is kept apart from the rest of the vault on purpose. Nothing in it is confirmed by the game. Every statement carries a tag:
> **[WIKI-REPORTED]** a fact a wiki states, quoted with its page and revision; **[THEORY]** something a person or video claims; **[UNREAD]** a source that exists but whose content could not be retrieved. Nothing here links to, or is linked from, the official notes.

# Unofficial - Source log

Everything that was tried for this section on 2026-10-07, what came back, and what could not be done. "Blocked" means a restriction in this environment or on the site's side; no attempt was made to get around any of them.

| Source | What happened | Used in this section? |
|---|---|---|
| Reddit (r/FearAndHunger and others) | The web-search tool refused with "The following domains are not accessible to our user agent: ['old.reddit.com', 'reddit.com']"; the page-fetch tool refused ("unable to fetch from www.reddit.com"); direct requests from the shell were refused (HTTP 403). Reddit pages were **not** pulled through archive copies or mirrors, because that would route around the site's own restriction. Later I tried `old.reddit.com` with an honest identifying user agent: every request (a subreddit page and a search page) was redirected (HTTP 302) to a login page titled "Welcome to Reddit". Going further would need a Reddit login, so I stopped. | No |
| X (Twitter) post by "Mauthe Doog" | The page is blocked by this environment's network policy. Only the post's text, as displayed in a web-search result title, was seen. | Yes, as a snippet, tagged [THEORY] |
| YouTube transcripts | The transcript library failed with "YouTube is blocking requests from your IP"; the video page itself answered "Sign in to confirm you're not a bot". Third-party transcript sites and proxies were not used, to avoid evading that block. | No |
| YouTube search results | Readable. Titles, channels, lengths and listed ages were recorded. | Yes, in the watchlist (metadata only) |
| Steam discussion threads (Fear & Hunger and Termina) | Four threads that a web search returned were requested; Steam answered with its generic error page for each (likely age-gating or login). | No |
| DeviantArt journal "Explaining Fear and Hunger's Lore and Story" by Xela-The-Conqueror (2023-08-26) | Readable. It is a plot recap and does not mention Amon or a Star God. | No |
| Main wiki (fearandhunger.wiki.gg) | Readable through its API. Searched all namespaces (articles, Talk, User, User blog, Message Wall, etc.) for "Amon", "Star God", "star god", "sun god", "stars"; nothing turned up outside article pages. | Yes, [WIKI-REPORTED] quotes: Amon, Abyssonia, Book of enlightenment, Golden Gates, Joy mask, Heartless One, Skin Bible - Rher, Per'kele/Dialogue |
| Tormentpedia (fearandhunger.fandom.com) | Readable through its API. Searched all namespaces for the same terms; its *The Gods* page has a section "Unnamed Sun God (Amon)" (used); the cut book page was read in full. Its "Lore/Theories" page is only a redirect to a page called "Theories", which does not exist. | Yes, the cut book, [WIKI-REPORTED] |
| Web search summaries | The search tool's own summaries paraphrase sources. One repeated the Tormentpedia's claim that "according to the Skin Bible - Rher, the sun is also a deity"; the Skin Bible's own text (main wiki transcription) says only "Very much like the sun - the moon is one of the primordial entities…", so that claim is the Tormentpedia's inference. **Summaries were not used as evidence**; only URLs, titles and exact page text were. | No |

## Retrieval dates and revisions
- Main wiki *The Gods*: revision 49336; *Abyssonia*: 48690; *Book of enlightenment*: 47771; *Golden Gates*: 49273; *Joy mask*: 49274; *Heartless One*: 49205; *Skin Bible - Rher*: 42648; *Per'kele/Dialogue*: 46903.
- Tormentpedia *The Gods*: revision 16519 (2026-06-11); *Seildna Modnaf Dilemna*: revision 16341 (2025-08-24).
- All retrieved 2026-10-07.
