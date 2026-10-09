import os
import sys
import json
import importlib.util
from concurrent.futures import ThreadPoolExecutor

import pytest
from tf.fabric import Fabric

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAM = os.path.join(ROOT_DIR, 'programs', 'tfFromGoettingen.py')

spec = importlib.util.spec_from_file_location('tfFromGoettingen', PROGRAM)
converter = importlib.util.module_from_spec(spec)
sys.modules['tfFromGoettingen'] = converter
spec.loader.exec_module(converter)

TRADITIONS = [
    {'slug': 'lxx-edition', 'language': 'grc', 'displayOrder': 0},
    {'slug': 'secunda', 'language': 'heb-Latn', 'displayOrder': 3},
    {'slug': 'mt', 'language': 'heb', 'displayOrder': 2},
    {'slug': 'aquila', 'language': 'grc', 'displayOrder': 4},
    {'slug': 'notes', 'language': '', 'displayOrder': 11},
]
CODES = {'2Sam': '1010', 'Ps': '1025'}


def attestation(label):
    return {'witness': {'label': label} if label else None, 'rawName': label}


def reading(number, texts, sequence=0, witnesses=(), alternative=None, prefix=''):
    tokens = [{'id': number * 10 + index, 'text': text} for index, text in enumerate(texts)]
    if alternative is not None:
        for token in tokens:
            token['alternative'] = alternative
    return {
        'id': number,
        'sequence': sequence,
        'prefix': prefix,
        'attestations': [attestation(label) for label in witnesses],
        'tokens': tokens,
    }


def cell(tradition, *readings):
    return {'tradition': tradition, 'readings': list(readings)}


def passage(book, chapter, verse, segments):
    return {
        'passage': {
            'book': book,
            'chapter': chapter,
            'verse': verse,
            'versekey': f'{CODES[book]}{chapter:03}{verse:03}',
        },
        'traditions': TRADITIONS,
        'segments': [
            {
                'stichos': number,
                'label': label,
                'positions': [
                    {'position': place, 'cells': cells}
                    for place, cells in enumerate(positions, 1)
                ],
            }
            for number, label, positions in segments
        ],
    }


def write(folder, data):
    key = data['passage']
    path = folder / key['book'] / f"{key['chapter']:03}" / f"{key['versekey']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding='utf-8')


def source(tmp_path):
    folder = tmp_path / 'source'
    first = [
        cell('aquila', reading(3, ['ἐν'], witnesses=['1098', 'Field'], prefix='+')),
        cell('mt', reading(2, ['בַּעֲצַת'])),
        cell('lxx-edition', reading(1, ['ἐν', 'βουλῇ'], alternative=False)),
    ]
    second = [cell('mt', reading(5, ['עַמִּים'], sequence=1), reading(4, ['רְשָׁעִים']))]
    third = [cell('mt', reading(6, [''], alternative=True))]
    write(folder, passage('Ps', 1, 1, [(1, 'a', [first, second]), (2, 'b', [third])]))
    write(folder, passage('Ps', 0, 0, [(1, '', [[cell('notes', reading(7, ['Psalmi']))]])]))
    samuel = [[cell('mt', reading(8, ['וַיְהִי'], witnesses=[''])), cell('aquila', reading(9, []))]]
    write(folder, passage('2Sam', 1, 1, [(1, 'a', samuel)]))
    return folder


def build(tmp_path):
    target = tmp_path / 'tf'
    assert converter.convert(source(tmp_path), target, ThreadPoolExecutor)
    return Fabric(locations=str(target), silent='deep').loadAll(silent='deep')


def test_passage_rows_give_one_row_per_reading_with_its_place_and_tokens(tmp_path):
    found = converter.passage_rows(source(tmp_path) / 'Ps' / '001' / '1025001001.json')
    assert found[0] == converter.Row(
        'aquila', 4, 'Psalmi', 1, 1, 1025001001, 1, 'a', 1, 0, 3,
        (('ἐν', 30, False),), ('1098', 'Field'), 'grc', '+',
    )
    assert [(row.tradition, row.position, row.sequence, row.reading) for row in found[1:]] == [
        ('mt', 1, 0, 2),
        ('lxx_edition', 1, 0, 1),
        ('mt', 2, 1, 5),
        ('mt', 2, 0, 4),
        ('mt', 1, 0, 6),
    ]


def test_passage_rows_reject_a_book_without_a_bhsa_name(tmp_path):
    path = tmp_path / 'x.json'
    data = passage('Ps', 1, 1, [(1, 'a', [[cell('mt', reading(1, ['א']))]])])
    data['passage']['book'] = 'Gen'
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(KeyError, match='Gen'):
        converter.passage_rows(path)


def test_line_breaks_write_every_line_break_as_a_newline():
    assert converter.line_breaks('a\r\nb\rc d\ne') == 'a\nb\nc\nd\ne'


def test_rows_order_traditions_then_passages_then_line_position_and_reading(tmp_path):
    with ThreadPoolExecutor() as pool:
        found = converter.rows(source(tmp_path), pool)
    keys = [(row.tradition, row.versekey, row.stichos, row.position, row.sequence) for row in found]
    assert keys == [
        ('lxx_edition', 1025001001, 1, 1, 0),
        ('mt', 1010001001, 1, 1, 0),
        ('mt', 1025001001, 1, 1, 0),
        ('mt', 1025001001, 1, 2, 0),
        ('mt', 1025001001, 1, 2, 1),
        ('mt', 1025001001, 2, 1, 0),
        ('aquila', 1010001001, 1, 1, 0),
        ('aquila', 1025001001, 1, 1, 0),
        ('notes', 1025000000, 1, 1, 0),
    ]


def test_convert_makes_each_tradition_a_text_with_its_books_chapters_and_verses(tmp_path):
    api = build(tmp_path)
    F, L, T, Fs = api.F, api.L, api.T, api.Fs
    assert [F.text.v(n) for n in F.otype.s('text')] == ['lxx_edition', 'mt', 'aquila', 'notes']
    mt = F.otype.s('text')[1]
    assert [F.book.v(n) for n in L.d(mt, 'book')] == ['Samuel_II', 'Psalmi']
    assert [Fs('book@en').v(n) for n in L.d(mt, 'book')] == ['2_Samuel', 'Psalms']
    verse = L.d(mt, 'verse')[1]
    assert T.sectionFromNode(verse) == ('mt', 'Psalmi', 1)
    assert (F.verse.v(verse), F.id.v(verse)) == (1, 1025001001)


def test_convert_keeps_the_inscriptio_as_chapter_0_verse_0(tmp_path):
    api = build(tmp_path)
    F, L = api.F, api.L
    (verse,) = L.d(F.otype.s('text')[3], 'verse')
    assert (F.chapter.v(L.u(verse, 'chapter')[0]), F.verse.v(verse)) == (0, 0)


def test_convert_makes_each_stichos_a_node_with_its_label_and_rank(tmp_path):
    api = build(tmp_path)
    F, L = api.F, api.L
    mt = F.otype.s('text')[1]
    found = [(F.stichos.v(n), F.rank.v(n)) for n in L.d(mt, 'stichos')]
    assert found == [('a', 1), ('a', 1), ('b', 2)]


def test_convert_makes_each_reading_a_word_group_with_id_rank_and_reading(tmp_path):
    api = build(tmp_path)
    F, L, T = api.F, api.L, api.T
    mt = F.otype.s('text')[1]
    groups = [(F.id.v(n), F.rank.v(n), F.reading.v(n), T.text(n)) for n in L.d(mt, 'word_group')]
    assert groups == [
        (8, 1, 0, 'וַיְהִי '),
        (2, 1, 0, 'בַּעֲצַת '),
        (4, 2, 0, 'רְשָׁעִים '),
        (5, 2, 1, 'עַמִּים '),
        (6, 1, 0, ' '),
    ]


def test_convert_lists_the_witnesses_of_a_reading_as_siglum(tmp_path):
    api = build(tmp_path)
    F, L = api.F, api.L
    group = L.d(F.otype.s('text')[2], 'word_group')[1]
    assert F.siglum.v(group) == '1098,Field'
    unnamed = L.d(F.otype.s('text')[1], 'word_group')[0]
    assert F.siglum.v(unnamed) is None


def test_convert_keeps_word_text_id_alternative_and_language(tmp_path):
    api = build(tmp_path)
    F = api.F
    words = [(F.text.v(n), F.id.v(n), F.alt.v(n), F.languageISO.v(n)) for n in F.otype.s('word')]
    assert words[:2] == [('ἐν', 10, None, 'grc'), ('βουλῇ', 11, None, 'grc')]
    assert ('', 60, 1, 'heb') in words
    assert words[-1] == ('Psalmi', 70, None, None)


def test_convert_gives_a_reading_without_tokens_one_empty_word(tmp_path):
    api = build(tmp_path)
    F, L = api.F, api.L
    empty = L.d(F.otype.s('text')[2], 'word_group')[0]
    assert F.id.v(empty) == 9
    (word,) = L.d(empty, 'word')
    assert (F.text.v(word), F.id.v(word)) == (None, None)


def test_convert_keeps_words_aligned_after_a_carriage_return(tmp_path):
    folder = tmp_path / 'source'
    write(folder, passage('Ps', 1, 1, [(1, 'a', [[cell('mt', reading(1, ['א\rב', 'ג']))]])]))
    assert converter.convert(folder, tmp_path / 'tf', ThreadPoolExecutor)
    api = Fabric(locations=str(tmp_path / 'tf'), silent='deep').loadAll(silent='deep')
    assert [api.F.text.v(n) for n in api.F.otype.s('word')] == ['א\nב', 'ג']


def test_convert_writes_the_attribution_and_license_into_the_metadata(tmp_path):
    build(tmp_path)
    otext = (tmp_path / 'tf' / 'otext.tf').read_text(encoding='utf-8')
    assert '@copynote1=Die Editio critica maior des griechischen Psalters.' in otext
    assert '@licenseUrl=https://creativecommons.org/licenses/by-nc-sa/4.0/' in otext


def test_main_reports_success_and_failure(tmp_path):
    folder = source(tmp_path)
    assert converter.main(['--source', str(folder), '--target', str(tmp_path / 'a')], ThreadPoolExecutor) == 0
    (tmp_path / 'empty').mkdir()
    empty = ['--source', str(tmp_path / 'empty'), '--target', str(tmp_path / 'b')]
    assert converter.main(empty, ThreadPoolExecutor) == 1


def test_text_names_are_snake_case():
    assert converter.text_name('field-latin') == 'field_latin'


def test_language_gives_the_secunda_greek_script():
    assert converter.language('heb-Latn') == 'heb-Grek'
    assert converter.language('grc') == 'grc'
    assert converter.language('') is None


def test_convert_removes_features_of_an_earlier_conversion(tmp_path):
    target = tmp_path / 'tf'
    target.mkdir()
    (target / 'line.tf').write_text('@node\n', encoding='utf-8')
    assert converter.convert(source(tmp_path), target, ThreadPoolExecutor)
    assert not (target / 'line.tf').exists()


def test_convert_keeps_the_prefix_of_a_reading(tmp_path):
    api = build(tmp_path)
    F, L = api.F, api.L
    groups = L.d(F.otype.s('text')[2], 'word_group')
    assert [F.prefix.v(g) for g in groups] == [None, '+']
