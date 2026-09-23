// The lexicon's PDF. Book structure comes from orange-book, which Quarto
// bundles; the palette, type, boxes, and table banding are the website's,
// carried over so the two editions read as one publication.
//
// This is a Pandoc template partial: dollar signs are template syntax.

#import "@preview/orange-book:0.7.1": book, chapter, appendices
#import "@preview/orange-book:0.7.1" as ob

// The lever palette is the book's spine: slate for the institutional levers,
// bronze for the physical ones. The rest are the site's table and box colors.
#let lex = (
  slate: rgb("#33506b"),
  bronze: rgb("#97783f"),
  link: rgb("#1f4f75"),
  ink: rgb("#2c2c2a"),
  muted: rgb("#6f6a5e"),
  rule: rgb("#9c927f"),
  head-fill: rgb("#efede8"),
  wash: rgb("#f6f5f1"),
)

// Set before the book so it reaches the cover and contents too. Source Sans
// is the website's face, committed in fonts/ so every build finds it.
#set text(
  font: "Source Sans 3",
  fill: lex.ink,
)

// Inter for everything that labels rather than reads: headings, the chapter
// panels, running heads, table headers, caption labels, page tabs. Source Sans
// stays the text face, matching the site.
#let display = "Inter"
#show heading: set text(font: display)

// orange-book puts the page number in the running head; Quarto's page setup
// adds a second one at the foot. Keep the head's.
#set page(footer: none)

#show: book.with(
$if(title)$
  title: [$title$],
$endif$
$if(subtitle)$
  subtitle: [$subtitle$],
$endif$
$if(by-author)$
  author: "$for(by-author)$$it.name.literal$$sep$, $endfor$",
$endif$
$if(date)$
  date: "$date$",
$endif$
  paper-size: "us-letter",
  margin: (x: 1.05in, top: 1.1in, bottom: 1in),
  font-size: 10.5pt,
  main-color: lex.slate,
  cover-background: lex.head-fill,
  cover: block(width: 100%, height: 100%, {
    place(top, rect(width: 100%, height: 2.6in, fill: lex.slate))
    place(top + left, pad(left: 0.9in, top: 1.05in, text(
      size: 11pt, weight: "semibold", tracking: 0.16em, fill: rgb("#c9d6e2"),
    )[WORKING DRAFT · CIRCULATED FOR COMMENT]))
    place(bottom + center, pad(x: 0.75in, bottom: 0.85in,
      image("figures/fig_scale_transect.svg", width: 100%, height: auto)))
  }),
  first-line-indent: false,
  heading-style: 2,
  copyright: none,
$if(toc-depth)$
  outline-depth: $toc-depth$,
$endif$
)

// ---- running head and page tab --------------------------------------------
// The chapter's title across the top, with its number only when it has one
// (orange-book's own head called the unnumbered Sources "Chapter 9"), and the
// page number in a slate tab on the outer edge, after the Extension guides.
#set page(
  header: context {
    let pg = here().page()
    if query(heading.where(level: 1)).any(h => h.location().page() == pg) { return }
    let prev = query(heading.where(level: 1).before(here()))
    if prev.len() == 0 { return }
    let ch = prev.last()
    set text(font: display, size: 8pt, weight: "semibold", tracking: 0.08em, fill: lex.muted)
    set par(justify: false)
    if ch.numbering != none {
      upper[Chapter #counter(heading).at(ch.location()).first()#h(0.6em)·#h(0.6em)#ch.body]
    } else {
      upper(ch.body)
    }
    v(-5pt)
    line(length: 100%, stroke: 0.4pt + rgb("#d3d1c7"))
  },
  footer: context {
    let pg = counter(page).get().first()
    let tab = box(fill: lex.slate, inset: (x: 8pt, y: 4pt), radius: 1.5pt,
      text(font: display, size: 8pt, weight: "semibold", fill: white, str(pg)))
    if calc.odd(pg) { align(right, tab) } else { align(left, tab) }
  },
)

// Our one appendix is the unnumbered A-Z index. Quarto announces it with an
// empty "Appendices" heading, which orange-book hides; keep it in the contents
// but give it no page of its own.
#let appendices(title, hide-parent: false, body) = {
  show heading.where(level: 1): it => {
    if it.body.at("text", default: none) == title { pagebreak(weak: true) } else { it }
  }
  body
}

// ---- parts ------------------------------------------------------------------
// orange-book's part page, less its rule that a part opens on a right-hand
// page, which left a blank page whenever the chapter before ended on one. Its
// small contents numbered the unnumbered chapters (Sources came out "10.5"),
// so the page lists the part's chapters itself.
#let part(title) = {
  pagebreak(weak: true)
  ob.part-change.update(true)
  ob.part-state.update(title)
  ob.part-counter.step()
  context ob.part-location.update(here())
  [#metadata(none)<lexicon-part>]
  context {
    let main-color = ob.main-color-state.get()
    set par(justify: false)
    place(block(width: 100%, height: 100%, outset: (x: 3cm, bottom: 2.5cm, top: 3cm), fill: main-color.lighten(70%)))
    place(top + right, text(font: display, fill: black, size: ob.large-text, weight: "bold", box(width: 60%, title)))
    place(top + left, text(fill: main-color, size: ob.part-font-size-state.get(), weight: "bold", ob.part-counter.display("I")))
    // This part's chapters: every chapter up to the next part, or to the
    // appendices after the last one.
    let next = query(selector(<lexicon-part>).after(here())).filter(m => m.location() != here())
    let chapters = query(if next.len() > 0 {
      selector(heading.where(level: 1)).after(here()).before(next.first().location())
    } else {
      selector(heading.where(level: 1)).after(here())
    })
    let listed = ()
    for h in chapters {
      if h.body.at("text", default: none) == "Appendices" { break }
      listed.push(h)
    }
    align(bottom + right, block(width: 9.5cm, {
      set text(font: display, size: 11pt)
      set align(left)
      line(length: 100%, stroke: 0.6pt + main-color)
      v(0.4em)
      grid(columns: (2em, 1fr, auto), row-gutter: 0.75em, column-gutter: 0.8em,
        ..listed.map(h => (
          if h.numbering != none { text(fill: main-color, weight: "bold", numbering("1", ..counter(heading).at(h.location()))) },
          link(h.location(), text(fill: lex.ink, weight: "semibold", h.body)),
          text(fill: lex.muted, str(h.location().page())),
        )).flatten())
    }))
  }
}

// ---- numbering and figures ------------------------------------------------
// Chapter numbers without orange-book's trailing period, which otherwise
// leaks into every cross-reference as "(§5.)".
#set heading(numbering: (..n) => {
  let v = n.pos()
  if v.len() == 1 { numbering("1", ..v) } else if v.len() <= 4 { numbering("1.1", ..v) }
})
// Figures float to the nearest top or bottom of a page they fit on, as in
// LaTeX, instead of leaving a gap wherever a large one will not fit.
#show figure.where(kind: "quarto-float-fig"): set figure(placement: auto)
// Tables are content here, not illustration, and several make up a whole
// section on their own. They stay where they are written and break across
// pages instead, repeating their header row.
#show figure.where(kind: "quarto-float-tbl"): set block(breakable: true)

// ---- body text ----------------------------------------------------------
// Paragraphs separated by space rather than indent, as on the site.
#set par(spacing: 0.95em, leading: 0.6em)
// Links read as ink with a quiet color, not the bright default blue.
#show link: set text(fill: lex.link)
#show cite: set text(fill: lex.muted)

// ---- chapter openers ----------------------------------------------------
// A slate panel with the chapter number, its title, and the sections inside
// it, after the Extension guides this edition takes its cue from. Replacing
// orange-book's opener also drops its rule that every chapter starts on a
// right-hand page, which left blank pages all through a PDF read on screen.
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  block(width: 100%, fill: lex.slate, radius: 2pt, inset: (x: 20pt, top: 18pt, bottom: 16pt), below: 0.4in, {
    set text(fill: white, font: display)
    set par(justify: false, leading: 0.5em)
    if it.numbering != none {
      text(size: 10pt, weight: "semibold", tracking: 0.16em, fill: rgb("#c9d6e2"))[
        CHAPTER #context counter(heading).display("1")
      ]
      v(3pt)
    }
    text(size: 25pt, weight: "bold", it.body)
    if it.numbering != none {
      context {
        let later = query(heading.where(level: 1).after(here())).filter(h => h.location() != here())
        let within = if later.len() > 0 {
          selector(heading.where(level: 2)).after(here()).before(later.first().location())
        } else {
          selector(heading.where(level: 2)).after(here())
        }
        let sections = query(within)
        if sections.len() > 0 {
          v(8pt)
          line(length: 100%, stroke: 0.5pt + rgb("#7d93a8"))
          v(2pt)
          set text(size: 9pt, weight: "semibold", tracking: 0.06em, fill: rgb("#dbe4ec"))
          for s in sections {
            let n = if s.numbering != none { numbering(s.numbering, ..counter(heading).at(s.location())) } else { "" }
            block(above: 4pt, below: 0pt, upper[#n#h(8pt)#s.body])
          }
        }
      }
    }
  })
}

// ---- captions -----------------------------------------------------------
// Supplement and number in slate, the caption itself a step smaller, set
// flush left so a long caption reads as a paragraph rather than a centered block.
#show figure.caption: it => {
  set text(size: 0.9em)
  set align(left)
  set par(justify: false)
  // Sticky: a table's caption sits above it, and should not be left behind at
  // the foot of one page while the table starts on the next.
  block(width: 100%, inset: (top: 2pt), sticky: true)[
    #text(font: display, weight: "semibold", fill: lex.slate)[#it.supplement #context it.counter.display(it.numbering)]#it.separator#it.body
  ]
}

// ---- the site's boxes ---------------------------------------------------
// A tinted panel with a colored rule down its left edge: green for a how-to,
// neutral for a worked example, amber for a caution.
#let lexicon-box-styles = (
  "how-to": (fill: rgb("#f6f9f1"), bar: rgb("#639922")),
  "example": (fill: lex.wash, bar: rgb("#a9a698")),
  "caution": (fill: rgb("#faf6ee"), bar: rgb("#b5843a")),
  "draft-note": (fill: lex.wash, bar: rgb("#d3d1c7")),
)

#let lexicon-box(kind, body) = {
  // A table or figure inside a box belongs to it. Left free to float, it
  // escaped the box and landed a page later without it.
  show figure: set figure(placement: none)
  if kind == "welcome" {
    block(width: 100%, below: 1.4em, text(size: 1.12em, body))
  } else {
    let s = lexicon-box-styles.at(kind)
    let small = kind == "caution" or kind == "draft-note"
    block(
      width: 100%,
      fill: s.fill,
      stroke: (left: 3pt + s.bar),
      inset: (x: 12pt, y: 10pt),
      radius: (right: 2pt),
      above: 1.2em,
      below: 1.2em,
      breakable: true,
      text(size: if small { 0.93em } else { 1em }, body),
    )
  }
}

// ---- the site's table banding -------------------------------------------
// Row colors carry meaning in this book: the zone greens, the diverging blue
// to purple of the farming axis, the pressures by direction. The PDF keeps them.
#let lexicon-bands = (
  "zone-table": ("#eaf3de", "#dcebc8", "#c0dd97", "#aed483", "#97c459"),
  "position-table": ("#6ba6d1", "#7fb3d9", "#bfdaec", "#efeeea", "#d9cbe6", "#b69ed4"),
  "function-table": ("#dce7ee", "#e0ebd3", "#eee7dc", "#d5e5e2"),
  "pressure-table": ("#d5e7e2", "#d5e7e2", "#d5e7e2", "#efeeea", "#efeeea", "#efeeea",
                     "#f4ded2", "#f4ded2", "#f4ded2"),
  "lever-table": ("#e8e6e1", "#f4eee2", "#eee5d3", "#e7dbc3", "#e4ebf1", "#d7e2ec"),
)

// Every table: the site's header row (small caps, warm gray, a rule beneath)
// and a quiet wash on alternate rows, so none is left in bare default dress.
#set table(
  inset: (x: 6pt, y: 5pt),
  fill: (x, y) => if y == 0 { lex.head-fill } else if calc.even(y) { lex.wash },
  stroke: (x, y) => if y > 1 { (top: 0.6pt + white) },
)
#set table.hline(stroke: 1.1pt + lex.rule)
#show table: set text(size: 0.9em)
#show table: set par(justify: false)
#show table.cell: set align(left)
#show table.cell.where(y: 0): it => {
  // Tracked capitals will not break mid-word on their own; a long header like
  // INTERCONNECTION in a narrow column ran into its neighbor.
  set text(font: display, size: 0.76em, weight: "semibold", fill: lex.muted, tracking: 0.03em, hyphenate: true)
  upper(it)
}

// Styled tables swap the wash for the bands that carry their meaning.
#let lexicon-table(kind, body) = {
  let bands = lexicon-bands.at(kind, default: none)
  if bands == none { return body }
  set table(fill: (x, y) => {
    if y == 0 { lex.head-fill } else { rgb(bands.at(calc.rem(y - 1, bands.len()))) }
  })
  body
}

// ---- callouts ---------------------------------------------------------------
// Quarto's callouts in the site's box idiom: a colored rule down the left edge
// and a tinted title band. The running example (Rabbit Hills) is the book's
// only tip callout, and takes the blue-violet it has on the site so it reads as
// one thread through the primer.
#let callout(body: [], title: "Callout", background_color: rgb("#dddddd"), icon: none, icon_color: black, body_background_color: white) = {
  let tip = background_color == rgb("#ccf1e3")
  let bar = if tip { rgb("#4f5b93") } else { icon_color }
  let band = if tip { rgb("#eceef6") } else { background_color.lighten(40%) }
  block(width: 100%, breakable: true, stroke: (left: 3pt + bar), radius: (right: 2pt), above: 1.2em, below: 1.2em, clip: true, {
    block(width: 100%, fill: band, inset: (x: 12pt, y: 7pt), below: 0pt, sticky: true,
      text(font: display, size: 0.9em, weight: "bold", fill: if tip { rgb("#333b6b") } else { lex.ink }, title))
    if body != [] { block(width: 100%, fill: lex.wash, inset: (x: 12pt, y: 9pt), above: 0pt, body) }
  })
}
