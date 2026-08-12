# The Lexicon of Restorative Agrisolar Design

A shared design language for agrisolar photovoltaic landscapes.

Published at <https://msuhydrogeology.github.io/restorative_agrisolar_lexicon/>

Built with [Quarto](https://quarto.org) as a book, rendered to a browsable HTML site and a
downloadable PDF from a single source.

## Publishing

Deployment is automatic. The GitHub Action in `.github/workflows/publish.yml` renders the book
(HTML + PDF) and deploys it to GitHub Pages on every push to `main`; pull requests are
render-checked but not deployed.

One-time repository setting: **Settings → Pages → Build and deployment → Source: GitHub Actions**.

## Local preview

Requires [Quarto](https://quarto.org/docs/get-started/) and `rsvg-convert` (from `librsvg`, for
embedding the SVG figures in the PDF). PDF output additionally needs a LaTeX install
(`quarto install tinytex`).

```bash
quarto preview        # live-reloading local site
quarto render         # build _site/ (HTML + PDF)
quarto render --to html   # HTML only (no LaTeX needed)
```

## Structure

| Path | Contents |
|---|---|
| `index.qmd` | Landing page |
| `scale-transect.qmd` … `sources.qmd` | Document chapters, one page each |
| `index-alphabetical.qmd` | Alphabetical index of defined terms (appendix) |
| `figures/` | Standalone SVG figures, reusable independently |
| `references.bib` | Bibliography; cited inline with `@key`, formatted in the Sources chapter |
| `_quarto.yml` | Book, format (HTML + PDF), and cross-reference configuration |

Cross-references between chapters use Quarto syntax: `@fig-transect` for figures and
`[text](file.qmd#sec-id)` for sections, with explicit `{#sec-…}` / `{#term-…}` heading ids so the
links stay stable. Sources are cited inline as `@key` against `references.bib`; the Sources chapter
keeps the curated, annotated Verified / Unverified lists alongside the generated reference list.

## Voice

The document is written for the people who adopt agrisolar rather than for a design profession:
farmers, community decision-makers, and solar design professionals. There is no agricultural
landscape design discipline to write to, let alone an agrisolar one. Prose should be recognizable
to a professional and readable by a landowner deciding what to do with forty acres.

The voice model is the REAL project description and Stid et al. (2025), *Impacts of agrisolar
co-location on the food–energy–water nexus and economic security* (`stid2025` in the
bibliography). Both are direct, evidence-first, and unhurried. The working rules:

- **No em-dashes in body prose.** They are the tell. Restructure the sentence, or use a comma, a
  colon, or a full stop. Dashes are fine as *structure* — glossary-entry openers, spec lines
  (`**Scale** — A3 · ~5–80 acres`), and table captions.
- **Long declarative paragraphs, built context → evidence → claim.** Around 80–90 words. Set the
  situation, bring the evidence, then say what follows.
- **Do not open paragraphs in bold.** Bold marks the load-bearing claim, a few times per chapter,
  plus structural labels (pressure names, `**Mechanism**` / `**Evidence status**`). A page of bold
  paragraph-openers is a tic, not emphasis.
- **End paragraphs on substance,** not on a reversal, a flourish, or a restatement.
- **Concrete over abstract.** Name the thing, give the number, say who it lands on. "Three ewes per
  acre" beats "appropriate stocking."
- **US English.** One standing exception: quoted titles keep their published spelling.
- **Pressures push. They do not pull.**
- **Describe, don't prescribe — but prescribe the aim, not the dimensions.** The lexicon holds a
  position on what agrisolar is *for*, and refuses to fix a clearance height.

Those rules catch tics at the sentence level. The harder failure is a paragraph that is fluent,
correct, and says nothing a reader can picture. Four more rules for that:

- **Show the instance, not the category.** "In California, groundwater law pays a grower to retire
  irrigated ground; in Iowa, the ethanol mandate pays them to keep planting it" beats "the
  direction is set by the jurisdiction." When a sentence describes the *shape* of a thing rather
  than the thing, put an example in its place. There should be a person, a place, a number, or an
  object in most paragraphs.
- **A cross-reference is not a description.** "(§4.5)" tells the reader where to look, not what is
  true. State the claim, then point.
- **"Not X, but Y" is a crutch.** The reversal reads as insight and usually isn't. Keep it where
  the contrast is the actual point; cut it where it is supplying rhythm. Same for "it is less about
  X than about Y" and "X rather than Y" used as a closing flourish.
- **Watch the balanced pair.** "Spreads good practice where the rule fits; locks in a bad fit where
  it does not." One of those is a sentence. Three in a row is a cadence the reader starts to hear,
  and it flattens real differences into symmetry.
- **Write for an interested technical reader, not for a software engineer.** Words borrowed from
  computing and systems design are precise to the people who use them and opaque to a township
  planner, a grazier, or an agronomist: *gates*, *registers*, *primitives*, *surfaces*, *parses*,
  *abstraction layer*. The same goes for imported social-science shorthand like *legible* and
  *apparatus*. Say what happens in the reader's own vocabulary. Not "the axis gates the functions"
  but "the axis decides which functions a site can deliver."

A rough check for the first rule, run from the repository root:

```bash
grep -n '—' chapters/*.qmd index.qmd | grep -vE ':[0-9]+:\s*([|*#-]|[0-9]+\.)'
```

Expect false positives on glossary openers and table captions, which are structural and fine. An
em-dash inside a running paragraph is not.

## Contributing

See `CONTRIBUTING.md`. Proposed terms, corrections, and counterexamples are all in scope —
particularly counterexamples to the claim, in *Which positions scale allows* in the farming-axis
chapter, that sparing is largely unavailable at A5.

## Citation

See `CITATION.cff`. For a stable citable version, connect the repository to Zenodo and cut a
release; Zenodo will mint a DOI and archive the snapshot.

## License

Content is licensed CC BY 4.0. See `LICENSE.md`.
