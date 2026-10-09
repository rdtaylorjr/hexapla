# Feature documentation

Here you find a description of the transcription of the Göttingen Hexapla Database,
the
[Text-Fabric model](https://annotation.github.io/text-fabric/tf/about/datamodel.html)
in general, and the node types and features of the Hexapla corpus in particular.

See also

*   [about](about.md) for the provenance of the data;
*   [TF docs](https://annotation.github.io/text-fabric/tf) for documentation on Text-Fabric.

## Transcription

The source is the Göttingen Hexapla Database, API version 3, one JSON file per passage,
for 2 Samuel and the Psalms. The database lays out every passage in stichoi, every stichos
in positions, and every position in cells, one per column: LXX Edition, Field (Ο′), MT,
Secunda, Aquila, Symmachus, Septuaginta (Origen), Quinta, Sexta, Θ acc. to Field, Others,
Notes, and Field (Latin). A cell holds one or more readings, and a reading holds tokens.

Every column becomes a [*text*](#node-type-text), following the
[ETCBC Targum corpus](https://github.com/ETCBC/targum), where every manuscript is a text.
The name of a text is the slug of its column in snake case, such as `lxx_edition`.
A stichos becomes a [*stichos*](#node-type-stichos), and a position becomes the `rank` of a
[*word_group*](#node-type-word_group) within its stichos. Where a cell holds more than one
reading, the readings share a rank and differ in `reading`, which keeps the `sequence` of
the database.

Chapter and verse numbers are those of the database, which uses Greek numbering. The title
of a psalm is verse 0. The inscriptio of a book is chapter 0, verse 0. Book names are those
of the BHSA.

The database labels the Secunda column `heb-Latn`. Its text is Hebrew in Greek letters,
so its `languageISO` is `heb-Grek`.

The token text is kept as given, including punctuation, sigla, and editorial brackets.
A carriage return and a line separator (U+2028) inside a token are written as a newline,
the line break that Text-Fabric can store in a feature value. This affects 5 tokens.

A reading without tokens is a word group of one empty word, without `text` and `id`.
This affects 4 readings in 2 Samuel.

## Text-Fabric model

The Text-Fabric model views the text as a series of atomic units, called
*slots*. In this corpus [*words*](#node-type-word) are the slots.

On top of that, more complex textual objects can be represented as *nodes*. In
this corpus we have node types for:

[*word*](#node-type-word),
[*word_group*](#node-type-word_group),
[*stichos*](#node-type-stichos),
[*verse*](#node-type-verse),
[*chapter*](#node-type-chapter),
[*book*](#node-type-book),
[*text*](#node-type-text).

The type of every node is given by the feature
[*`otype`*](https://annotation.github.io/text-fabric/tf/cheatsheet.html#f-node-features).
Every node is linked to a subset of slots by
[*`oslots`*](https://annotation.github.io/text-fabric/tf/cheatsheet.html#special-edge-feature-oslots).

Nodes can be annotated with features.
See the table below.

Text-Fabric supports up to three customisable section levels.
In this corpus we use
[*text*](#node-type-text), [*book*](#node-type-book), and [*chapter*](#node-type-chapter).

# Reference table of features

*(Keep this under your pillow)*

## *absent*

When we say that a feature is *absent* for a node, we mean that the node has no value
for the feature. For example, if the feature `alt` is absent for node `n`, then
`F.alt.v(n)` results in the Python value `None`, not the string `'None'`.

In queries, you can test for absence by means of `#`:

```
word alt#
```

gives all words where the feature `alt` is absent.

See also
[search templates](https://annotation.github.io/text-fabric/tf/about/searchusage.html)
under **Value specifications**.

## Node type [*word*](#word)

A token of the database.

feature | values | description
------- | ------ | ------
*`text`* | `μακάριος` `אַשְׁרֵי` | the text of the token as given in the database
*`trailer`* | ` ` | content after a word
*`id`* | `423858` | database id of the token
*`alt`* | `1` | the database marks the token as an alternative
*`languageISO`* | `grc` `heb` `heb-Grek` `lat` | language and script code of the column

## Node type [*word_group*](#word_group)

A reading of the database.

feature | values | description
------- | ------ | ------
*`id`* | `306188` | database id of the reading
*`rank`* | `1` `2` | position of the reading within its stichos
*`reading`* | `0` `1` | which reading at this position, 0 being the first
*`siglum`* | `1098,Field` | sigla of the witnesses attesting the reading, comma separated
*`prefix`* | `+` `pr` `cf.` | text printed before the reading: `+` marks an addition, `pr` material placed before

## Node type [*stichos*](#stichos)

A stichos of the database.

feature | values | description
------- | ------ | ------
*`stichos`* | `a` `b` | letter of the stichos, absent where the database gives none
*`rank`* | `1` `2` | number of the stichos within the verse

## Node type [*verse*](#verse)

A passage of the database.

feature | values | description
------- | ------ | ------
*`verse`* | `0` `1` | verse number in Greek numbering, 0 for a title or inscriptio
*`id`* | `1025001001` | API key of the passage

## Node type [*chapter*](#chapter)

Section level 3.

feature | values | description
------- | ------ | ------
*`chapter`* | `0` `1` | chapter number in Greek numbering, 0 for the inscriptio

## Node type [*book*](#book)

Section level 2.

feature | values | description
------- | ------ | ------
*`book`* | `Samuel_II` `Psalmi` | book name in Latin, as in the BHSA
*`book@en`* | `2_Samuel` `Psalms` | book name in English, as in the BHSA

## Node type [*text*](#text)

Section level 1.

feature | values | description
------- | ------ | ------
*`text`* | `lxx_edition` `mt` `secunda` `aquila` | column of the database, in snake case

# Text formats

The following text formats are defined (you can also list them with `T.formats`).

format | description
--- | ---
`text-orig-full`     | the text of all words, each followed by a space
