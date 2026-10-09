import os
import re
import json
import collections
from concurrent.futures import ProcessPoolExecutor

from tf.fabric import Fabric

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TF_FOLDER = 'tf'
SOURCE_FOLDER = 'source'
latest_data_folder = sorted(os.listdir(os.path.join(ROOT_DIR, TF_FOLDER)))[-1]
SOURCE_DIR = os.path.join(ROOT_DIR, SOURCE_FOLDER, latest_data_folder)

TF = Fabric(locations=os.path.join(ROOT_DIR, TF_FOLDER, latest_data_folder))
api = TF.load('''
    otype text book chapter verse stichos rank reading id siglum prefix alt languageISO
''')
api.loadLog()

F, L = api.F, api.L

BOOKS = {'2Sam': 'Samuel_II', 'Ps': 'Psalmi'}
LANGUAGES = {'heb-Latn': 'heb-Grek'}
LINE_BREAK = re.compile('\r\n|\r| ')


def sigla(attestations):
    labels = [(a['witness'] or {}).get('label') or a['rawName'] for a in attestations]
    return ','.join(label for label in labels if label) or None


def passage_readings(path):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    key = data['passage']
    language = {t['slug']: LANGUAGES.get(t['language'], t['language']) or None for t in data['traditions']}
    return [
        (
            cell['tradition'].replace('-', '_'), BOOKS[key['book']], key['chapter'], key['verse'],
            int(key['versekey']), segment['stichos'], segment['label'] or None,
            place['position'], reading['sequence'], reading['id'],
            tuple(
                (LINE_BREAK.sub('\n', token['text']), token['id'],
                 1 if token.get('alternative') else None, language[cell['tradition']])
                for token in reading['tokens']
            ),
            sigla(reading['attestations']),
            reading['prefix'] or None,
        )
        for segment in data['segments']
        for place in segment['positions']
        for cell in place['cells']
        for reading in cell['readings']
    ]


def source_readings():
    paths = sorted(
        os.path.join(root, name)
        for root, _, names in os.walk(SOURCE_DIR)
        for name in names
        if name.endswith('.json')
    )
    with ProcessPoolExecutor() as pool:
        parts = pool.map(passage_readings, paths, chunksize=64)
        return collections.Counter(row for part in parts for row in part)


def tf_readings():
    result = collections.Counter()
    for g in F.otype.s('word_group'):
        verse, stichos = L.u(g, 'verse')[0], L.u(g, 'stichos')[0]
        words = [w for w in L.d(g, 'word') if F.id.v(w) is not None]
        result[(
            F.text.v(L.u(g, 'text')[0]), F.book.v(L.u(g, 'book')[0]),
            F.chapter.v(L.u(g, 'chapter')[0]), F.verse.v(verse), F.id.v(verse),
            F.rank.v(stichos), F.stichos.v(stichos), F.rank.v(g), F.reading.v(g), F.id.v(g),
            tuple((F.text.v(w) or '', F.id.v(w), F.alt.v(w), F.languageISO.v(w)) for w in words),
            F.siglum.v(g),
            F.prefix.v(g),
        )] += 1
    return result


def test_every_reading_of_the_source_is_a_word_group_with_the_same_content():
    assert source_readings() == tf_readings()


def test_every_word_group_has_at_least_one_word():
    assert all(L.d(g, 'word') for g in F.otype.s('word_group'))
