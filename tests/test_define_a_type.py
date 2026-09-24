from pytest_bdd import scenarios, then, when

from calls import create, define, read

scenarios("define-a-type.feature")

NOTE_TYPE = {
    "title": "Note",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "body": {"type": "string"},
            "relates_to": {
                "type": "string",
                "ref": {"targets": ["note"], "cardinality": "one", "parts": False, "on_delete": "refuse"},
            },
        },
        "required": ["title"],
        "sections": [{"title": "Context"}, {"title": "Outcome"}],
        "parts": {
            "attachments": {
                "items": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "url": {"type": "string"}},
                    "required": ["title"],
                }
            }
        },
        "summary": ["relates_to"],
    },
}


@when(
    "the client defines a type whose artifacts carry a title, a body, a link to another artifact "
    "of the same type, two required sections in order, and a collection of parts",
    target_fixture="defined",
)
def _define_note(client):
    return define(client, NOTE_TYPE)


@then("the type is an artifact the client can read back like any other")
def _read_back_like_any_other(client, defined):
    assert defined.id == "schema/note"
    note_type = read(client, defined.id)
    assert (note_type.id, note_type.type, note_type.title) == ("schema/note", "schema", "Note")
    assert note_type.revision == 1


@then("artifacts of that type can be created")
def _create_a_note(client):
    note = create(client, "note", {
        "title": "First note",
        "body": "A note to start with.\n",
        "sections": [
            {"title": "Context", "body": "Why the note exists.\n"},
            {"title": "Outcome", "body": "What came of it.\n"},
        ],
        "attachments": [{"title": "Sketch", "url": "https://example.test/sketch"}],
    })
    assert note.id == "note/first-note"
    assert note.revision == 1
