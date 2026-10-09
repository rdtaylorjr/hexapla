"""Converts the Göttingen Hexapla Database download to Text-Fabric."""

from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import Executor, ProcessPoolExecutor
from itertools import groupby
from operator import attrgetter
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Any, NamedTuple

from tf.convert.walker import CV
from tf.fabric import Fabric

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

ORG = "rdtaylorjr"
REPO = "hexapla"
VERSION = "0.1"

BASE = Path("~/github").expanduser()
REPO_DIR = BASE / ORG / REPO
SOURCE_DIR = REPO_DIR / "source" / VERSION
TF_DIR = REPO_DIR / "tf" / VERSION
PASSAGES = "*/*/*.json"
CHUNK = 64

BOOKS = {"2Sam": "Samuel_II", "Ps": "Psalmi"}
BOOKS_EN = {"Samuel_II": "2_Samuel", "Psalmi": "Psalms"}
LANGUAGES = {"heb-Latn": "heb-Grek"}
LINE_BREAK = re.compile("\r\n|\r|\u2028")

slotType = "word"

generic = {
    "name": "Hexapla",
    "source": "Göttingen Hexapla Database, API version 3",
    "sourceUrl": "https://septuaginta.uni-goettingen.de/api/hexapla/v3/",
    "sourceFormat": "JSON",
    "compiler": "Niedersächsische Akademie der Wissenschaften zu Göttingen",
    "converters": "Rusty Taylor",
    "license": "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International",
    "licenseUrl": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "copynote1": (
        "Die Editio critica maior des griechischen Psalters."
        " Niedersächsische Akademie der Wissenschaften zu Göttingen."
    ),
    "copynote2": "© Göttingen Academy of Sciences and Humanities in Lower Saxony",
    "copynote3": (
        "Modified: converted from JSON to Text-Fabric, see docs/transcription.md."
        " Provided as is, without warranties, see the disclaimer in the license."
    ),
    "version": VERSION,
}

otext = {
    "sectionTypes": "text,book,chapter",
    "sectionFeatures": "text,book,chapter",
    "fmt:text-orig-full": "{text}{trailer}",
}

intFeatures = {"alt", "chapter", "id", "rank", "reading", "verse"}

featureMeta = {
    "alt": {"description": "alternative reading", "values": "1"},
    "book": {"description": "book name in Latin, as in the BHSA"},
    "book@en": {
        "description": "book name in english, as in the BHSA",
        "language": "English",
        "languageCode": "en",
        "languageEnglish": "english",
    },
    "chapter": {"description": "Chapter of the book in Greek numbering, 0 for the inscriptio"},
    "id": {"description": "database id, associated to primary key in the Göttingen database"},
    "languageISO": {"description": "language and script code of the text"},
    "stichos": {"description": "letter of a stichos within the verse"},
    "prefix": {"description": "text printed before the reading, such as + or pr"},
    "rank": {
        "description": (
            "ordinal position of the node among its siblings, counting from the start"
            " of the enclosing node, within the stichos"
        )
    },
    "reading": {
        "description": (
            "which reading of a word group this is; readings at one position of the stichos"
            " share a rank and differ here, 0 being the first"
        )
    },
    "siglum": {"description": "sigla of the witnesses attesting the reading (comma separated)"},
    "text": {"description": "Name of a column of the database, or the text of a word"},
    "trailer": {"description": "Content after a word (empty space or None)"},
    "verse": {"description": "Verse of the chapter in Greek numbering, 0 for the title"},
}

Token = tuple[str, int, bool]


class Row(NamedTuple):
    """One reading of one tradition with its place in the database layout and its tokens."""

    tradition: str
    order: int
    book: str
    chapter: int
    verse: int
    versekey: int
    stichos: int
    label: str
    position: int
    sequence: int
    reading: int
    tokens: tuple[Token, ...]
    sigla: tuple[str, ...]
    language: str | None
    prefix: str


def passage_rows(path: Path) -> list[Row]:
    """Reads one passage file into rows in source order."""
    data = json.loads(path.read_text(encoding="utf-8"))
    key = data["passage"]
    traditions = {tradition["slug"]: tradition for tradition in data["traditions"]}
    return [
        Row(
            text_name(cell["tradition"]),
            traditions[cell["tradition"]]["displayOrder"],
            BOOKS[key["book"]],
            key["chapter"],
            key["verse"],
            int(key["versekey"]),
            segment["stichos"],
            segment["label"],
            place["position"],
            item["sequence"],
            item["id"],
            tuple(
                (line_breaks(token["text"]), token["id"], bool(token.get("alternative")))
                for token in item["tokens"]
            ),
            tuple(_sigla(item["attestations"])),
            language(traditions[cell["tradition"]]["language"]),
            item["prefix"],
        )
        for segment in data["segments"]
        for place in segment["positions"]
        for cell in place["cells"]
        for item in cell["readings"]
    ]


def text_name(slug: str) -> str:
    """Writes a column slug of the database in snake case."""
    return slug.replace("-", "_")


def language(code: str) -> str | None:
    """Gives the language and script code of a column, the Secunda in Greek script."""
    return LANGUAGES.get(code, code) or None


def line_breaks(text: str) -> str:
    """Writes every line break as the newline that Text-Fabric escapes in feature values."""
    return LINE_BREAK.sub("\n", text)


def rows(source: Path, executor: Executor) -> list[Row]:
    """Reads every passage across workers and orders the rows by text, passage, and place."""
    paths = sorted(source.glob(PASSAGES), key=lambda path: path.stem)
    found = [row for part in executor.map(passage_rows, paths, chunksize=CHUNK) for row in part]
    return sorted(found, key=attrgetter("order", "versekey", "stichos", "position", "sequence"))


def director(cv: Any, source: Iterable[Row]) -> None:
    """Emits the text, book, chapter, verse, stichos, word group, and word nodes of the rows."""
    for tradition, in_text in groupby(source, key=attrgetter("tradition")):
        text = cv.node("text")
        cv.feature(text, text=tradition)
        for book, in_book in groupby(in_text, key=attrgetter("book")):
            book_node = cv.node("book")
            cv.feature(book_node, **{"book": book, "book@en": BOOKS_EN[book]})
            for chapter, in_chapter in groupby(in_book, key=attrgetter("chapter")):
                chapter_node = cv.node("chapter")
                cv.feature(chapter_node, chapter=chapter)
                for _, in_verse in groupby(in_chapter, key=attrgetter("versekey")):
                    _verse(cv, list(in_verse))
                cv.terminate(chapter_node)
            cv.terminate(book_node)
        cv.terminate(text)
    for name in featureMeta:
        if not cv.occurs(name):
            cv.meta(name)


def _verse(cv: Any, readings: list[Row]) -> None:
    """Emits one verse node with its stichoi and word groups."""
    verse = cv.node("verse")
    cv.feature(verse, verse=readings[0].verse, id=readings[0].versekey)
    for _, in_stichos in groupby(readings, key=attrgetter("stichos")):
        group = list(in_stichos)
        stichos = cv.node("stichos")
        cv.feature(stichos, stichos=group[0].label or None, rank=group[0].stichos)
        for row in group:
            _word_group(cv, row)
        cv.terminate(stichos)
    cv.terminate(verse)


def _word_group(cv: Any, row: Row) -> None:
    """Emits one word group with its words."""
    node = cv.node("word_group")
    cv.feature(
        node,
        id=row.reading,
        rank=row.position,
        reading=row.sequence,
        siglum=",".join(row.sigla) or None,
        prefix=row.prefix or None,
    )
    if not row.tokens:
        word = cv.slot()
        cv.feature(word, trailer=" ")
    for text, number, alternative in row.tokens:
        word = cv.slot()
        cv.feature(
            word,
            text=text,
            id=number,
            trailer=" ",
            alt=1 if alternative else None,
            languageISO=row.language,
        )
    cv.terminate(node)


def _sigla(attestations: Iterable[dict[str, Any]]) -> Iterable[str]:
    """Yields the label of each attesting witness that has a name."""
    for entry in attestations:
        label = (entry["witness"] or {}).get("label") or entry["rawName"]
        if label:
            yield label


def languages(found: Iterable[Row]) -> str:
    """Lists the language codes of the rows, without their script, as the metadata of the dataset."""
    return ",".join(sorted({row.language.split("-")[0] for row in found if row.language}))


def convert(
    source: Path = SOURCE_DIR,
    target: Path = TF_DIR,
    executor: Callable[[], Executor] = ProcessPoolExecutor,
) -> bool:
    """Writes the Text-Fabric dataset of the source folder to the target folder."""
    with executor() as pool:
        found = rows(source, pool)
    if target.exists():
        rmtree(target)
    cv = CV(Fabric(locations=str(target), silent="deep"), silent="deep")
    return bool(
        cv.walk(
            lambda walker: director(walker, found),
            slotType,
            otext=otext,
            generic={**generic, "language": languages(found)},
            intFeatures=intFeatures,
            featureMeta=featureMeta,
        )
    )


def main(
    argv: list[str] | None = None, executor: Callable[[], Executor] = ProcessPoolExecutor
) -> int:
    """Converts the source given on the command line, or the source of this version."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_DIR)
    parser.add_argument("--target", type=Path, default=TF_DIR)
    args = parser.parse_args(argv)
    return 0 if convert(args.source, args.target, executor) else 1


if __name__ == "__main__":
    raise SystemExit(main())
