// Szablon Pracy Dyplomowej w Typst (Standard 2027)
// Wersja: 1.0 - Zgodna z wymogami uczelni technicznych

#let thesis_template(
  title: "Tytuł Pracy Dyplomowej",
  subtitle: none,
  author: "Imię i Nazwisko",
  supervisor: "dr inż. Promotor Akademicki",
  institution: "Politechnika / Uczelnia Techniczna",
  faculty: "Wydział Informatyki",
  field_of_study: "Informatyka Stosowana",
  year: 2027,
  abstract: none,
  keywords: (),
  body
) = {
  set document(title: title, author: author)
  set page(
    paper: "a4",
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3.0cm, right: 2.0cm),
    header: locate(loc => {
      if loc.page() > 2 [
        #smallcaps(title)
        #line(length: 100%, stroke: 0.5pt)
      ]
    }),
    footer: locate(loc => {
      if loc.page() > 2 [
        #align(center)[#loc.page()]
      ]
    })
  )
  
  set text(font: "Linux Libertine", size: 11pt, lang: "pl")
  set par(justify: true, leading: 0.75em, first-line-indent: 1.25cm)
  set heading(numbering: "1.1")

  // Strona tytułowa
  align(center)[
    #text(14pt, weight: "bold")[#institution]\
    #text(12pt)[#faculty]\
    #v(3cm)
    #text(20pt, weight: "bold")[#title]\
    #if subtitle != none [
      #v(0.5cm)
      #text(13pt, style: "italic")[#subtitle]
    ]
    #v(2.5cm)
    #text(13pt, weight: "bold")[Praca Dyplomowa Inżynierska]\
    #text(11pt)[Kierunek: #field_of_study]\
    #v(3cm)
    #grid(
      columns: (1fr, 1fr),
      align: (left, right),
      [Autor:\ *#author*],
      [Promotor:\ *#supervisor*]
    )
    #v(2cm)
    #text(11pt)[Warszawa, #year]
  ]
  pagebreak()

  // Streszczenie
  if abstract != none [
    #heading(numbering: none)[Streszczenie]
    #abstract
    #if keywords.len() > 0 [
      \ \ *Słowa kluczowe:* #keywords.join(", ")
    ]
    #pagebreak()
  ]

  // Spis treści
  outline(title: [Spis treści], indent: auto)
  pagebreak()

  body
}

