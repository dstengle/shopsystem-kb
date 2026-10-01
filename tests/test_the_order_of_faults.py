"""The order faults come in, beyond the scenarios: an entry of any list ranks by its index as a number, at any level,
an ordinary list field's as a collection's; the whole artifact's faults before any inside it; a missing section
before the collections. Through Create and Check, and for a type, through its definition. Each store under its own
tmp_path."""
import pytest

from calls import check, create, define, request, start_a_store
import held
from kb import client as kb_client

TITLE = {"title": {"type": "string"}}

NOTE_TYPE = {
    "title": "Note",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {**TITLE, "tags": {"type": "array", "items": {"type": "string", "maxLength": 3}}},
        "required": ["title", "owner"],
        "sections": [{"title": "Context"}],
        "parts": {"options": {"items": {"type": "object", "properties": TITLE, "required": ["title"]}}},
    },
}

# Eleven of each, the third and the eleventh breaking the type, so text order and number order differ.
TAGS = ["ok"] * 11
TAGS[2] = TAGS[10] = "too long"
OPTIONS = [{"title": "One"} for _ in range(11)]
OPTIONS[2] = OPTIONS[10] = {"title": 7}

NESTED_SECTIONS = [
    {"title": "Context", "body": "Why.\n", "sections": [{"title": "Background", "body": 5}]},
    {"title": "More", "body": 6},
]

IN_THE_SECTIONS = (
    {"tags": TAGS, "sections": NESTED_SECTIONS, "options": OPTIONS},
    [
        ("", "required"), ("tags/2", "maxLength"), ("tags/10", "maxLength"),
        ("sections/0/sections/0/body", "type"), ("sections/1/body", "type"),
        ("options/2/title", "type"), ("options/10/title", "type"),
    ],
)
WITHOUT_SECTIONS = (
    {"owner": "Ops", "options": OPTIONS},
    [("sections", "sections"), ("options/2/title", "type"), ("options/10/title", "type")],
)
CASES = {"faults inside the sections": IN_THE_SECTIONS, "the sections left out": WITHOUT_SECTIONS}


@pytest.fixture
def client(root):
    connected = kb_client.connect(root)
    start_a_store(root)
    define(connected, NOTE_TYPE)
    return connected


def _faults(faults):
    return [(fault.place, fault.rule) for fault in faults]


def test_an_ordinary_list_fields_entries_come_in_number_order(client):
    refused = request(client, "note", "Tagged", {"owner": "Ops", "tags": TAGS, "sections": [
        {"title": "Context", "body": "Why.\n"},
    ]})
    assert _faults(refused.faults) == [("tags/2", "maxLength"), ("tags/10", "maxLength")]


def test_a_types_members_naming_no_type_come_in_number_order(client):
    members = [{"$ref": "kb:schema/note"}] * 11
    members[2] = {"$ref": "kb:schema/nothing"}
    members[10] = {"$ref": "kb:schema/nowhere"}
    refused = request(client, "schema", "Memo", {"version": 1, "schema": {"allOf": members}}, message="Define Memo")
    assert _faults(refused.faults) == [("schema/allOf/2/$ref", "shape"), ("schema/allOf/10/$ref", "shape")]


@pytest.mark.parametrize("case", CASES)
def test_a_refused_create_gives_its_faults_in_reading_order(client, case):
    content, expected = CASES[case]
    assert _faults(request(client, "note", "Ordered", content).faults) == expected


@pytest.mark.parametrize("case", CASES)
def test_a_check_gives_an_artifacts_violations_in_reading_order(root, client, case):
    content, expected = CASES[case]
    made = create(client, "note", {"title": "Ordered", "owner": "Ops", "sections": [
        {"title": "Context", "body": "Why.\n"},
    ]})
    stored = held.artifact(root, made.id)
    identity = {key: stored[key] for key in ("id", "type", "schema_version", "revision", "title")}
    held.plant(root, made.id, {**identity, **content})
    assert _faults(check(client).violations) == expected
