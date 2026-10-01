"""Pins the bytes of `canonical.dump`. The emitter's exact output is not ruamel's published contract, yet it feeds
every digest and the exported files, so a release of ruamel that moves one byte must fail here."""
from kb import canonical

ARTIFACT = {
    "title": "A golden artifact",
    "kind": "note",
    "version": 3,
    "published": True,
    "reviewed": "2026-10-01",
    "tags": ["alpha", "beta"],
    "summary": {"body": "Short."},
    "sections": [
        {"name": "Long", "body": "word " * 40 + "end\nsecond line"},
        {"name": "Empty", "body": ""},
    ],
}

GOLDEN = (
    'title: A golden artifact\n'
    'kind: note\n'
    'version: 3\n'
    'published: true\n'
    "reviewed: '2026-10-01'\n"
    'tags:\n'
    '  - alpha\n'
    '  - beta\n'
    'summary:\n'
    '  body: |-\n'
    '    Short.\n'
    'sections:\n'
    '  - name: Long\n'
    '    body: |-\n'
    '      word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word word end\n'
    '      second line\n'
    '  - name: Empty\n'
    '    body: |\n'
)


def test_the_canonical_dump_of_an_artifact_is_these_bytes():
    assert canonical.dump(ARTIFACT) == GOLDEN
