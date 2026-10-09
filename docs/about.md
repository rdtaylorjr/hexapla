# About the Hexapla

The source of this dataset is the Göttingen Hexapla Database of the
Niedersächsische Akademie der Wissenschaften zu Göttingen, API version 3,
`https://septuaginta.uni-goettingen.de/api/hexapla/v3/?versekey=<versekey>`.

The database places every Hexaplaric reading beside the LXX edition, Field's Ο′, and the MT,
stichos by stichos and word position by word position, and records the manuscript witnesses
of every reading.

# Corpus

The [source](../source) directory contains the JSON files of the database, one file per
passage: 696 passages of 2 Samuel and 2,678 passages of the Psalms.

These files have been converted into Text-Fabric format by
[tfFromGoettingen.py](../programs/tfFromGoettingen.py).
We have a [specification](transcription.md) of how we model the text in Text-Fabric.
The conversion result is available in the [tf](../tf) directory.

The database also records the folio, Aristarchian sign, note, and attributed translator of
every attestation, editorial notes of readings, notes of tokens, scholarly
attributions, review states, and legacy ids. These are not included in the Text-Fabric data.
They remain in the source files.

# License and citation

The Göttingen Hexapla Database is created by the Niedersächsische Akademie der Wissenschaften
zu Göttingen, which publishes its data under the
[CC BY-NC-SA 4.0 license](https://creativecommons.org/licenses/by-nc-sa/4.0/)
([imprint](https://septuaginta.uni-goettingen.de/imprint/)).
Every response of the database carries the copyright notice

```
Die Editio critica maior des griechischen Psalters. Niedersächsische Akademie der Wissenschaften zu Göttingen.
```

and the database site carries the notice

```
© Göttingen Academy of Sciences and Humanities in Lower Saxony
```

The files in [source](../source) are the database responses as downloaded, without
modification.

The Text-Fabric data in [tf](../tf) is a modified form of these files:

*   the data is converted from JSON to Text-Fabric, with every column a text named in snake
    case, every stichos a stichos node, and every reading a word group;
*   the language code of the Secunda is given as `heb-Grek` for `heb-Latn`;
*   books are named as in the BHSA, in Latin in `book` and in English in `book@en`;
*   carriage returns and line separators inside a token are written as newlines;
*   a reading without tokens is given one empty word;
*   the fields listed under [Corpus](#corpus) are left out.

The [transcription](transcription.md) describes the conversion in full.

The source files and the Text-Fabric data are licensed under the
[CC BY-NC-SA 4.0 license](https://creativecommons.org/licenses/by-nc-sa/4.0/),
see [LICENSE](../LICENSE). They are provided as is, without warranties of any kind,
as stated in Section 5 of the license. You may not use them for commercial purposes.
