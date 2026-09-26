import re

from pytest_bdd import given, parsers, scenarios, then, when

from calls import create, define, everything_under, read, request
from kb import canonical

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


TOOL_TYPE = {
    "title": "Tool",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "$defs": {
            "binding": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "value": {"type": "string"}},
                "required": ["name", "value"],
                "additionalProperties": False,
            },
        },
    },
}

TOOL_USE_TYPE = {
    "title": "Tool use",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "bindings": {"type": "array", "items": {"$ref": "kb:schema/tool#/$defs/binding"}},
        },
        "required": ["title"],
    },
}


@given("a type that defines the shape of a binding")
def _a_type_defining_a_binding(client):
    define(client, TOOL_TYPE)


@when("the client defines a second type that refers to that shape")
def _define_a_type_referring_to_it(client):
    define(client, TOOL_USE_TYPE)


@then("artifacts of the second type are checked against the shape the first type defines")
def _checked_against_the_shared_shape(client):
    fits = request(client, "tool-use", "Weigh the flour", {"bindings": [{"name": "scale", "value": "kitchen"}]})
    assert not fits.faults, fits.faults
    misfit = request(client, "tool-use", "Weigh the sugar", {"bindings": [{"name": "scale"}]})
    assert (misfit.id, misfit.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in misfit.faults] == [("bindings/0", "required")]
    assert "'value' is a required property" in misfit.faults[0].message


BASE_TYPE = {
    "title": "Base",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"owner": {"type": "string"}, "status": {"type": "string"}},
        "required": ["owner", "status"],
        "sections": [{"title": "Purpose"}],
    },
}

DECISION_ON_BASE_TYPE = {
    "title": "Decision",
    "version": 1,
    "schema": {
        "allOf": [{"$ref": "kb:schema/base"}],
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "sections": [{"title": "Rationale"}],
    },
}

BASE_SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@given(
    "a base type that gives every artifact an owner and a status, and requires a purpose section"
)
def _a_base_type(client):
    define(client, BASE_TYPE)


@when("the client defines a decision type built on that base, adding a rationale section of its own")
def _define_a_decision_on_the_base(client):
    define(client, DECISION_ON_BASE_TYPE)


@then("a decision missing its owner is rejected because it does not fit its type")
def _rejected_without_an_owner(client):
    refused = request(client, "decision", "Price reviews happen weekly", {"status": "accepted", "sections": BASE_SECTIONS})
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in refused.faults] == [("", "required")]
    assert "'owner' is a required property" in refused.faults[0].message


@then("a decision reads back with its purpose before its rationale")
def _purpose_before_rationale(root, client):
    created = request(client, "decision", "Price reviews happen weekly", {
        "owner": "shopkeeper", "status": "accepted", "sections": BASE_SECTIONS,
    })
    assert not created.faults, created.faults
    on_disk = canonical.load((root / "kb" / f"{created.id}.yaml").read_text())
    assert [section["title"] for section in on_disk["sections"]] == ["Purpose", "Rationale"]


@when("the client defines a type that does not match the type that describes types", target_fixture="refused")
def _define_a_malformed_type(client):
    return request(client, "schema", "Shelf label", {"version": 1, "schema": {"type": "label"}}, message="Define Shelf label")


@then("the type is rejected because it does not match the type that describes types")
def _rejected_by_the_metaschema(client, refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [
        ("schema/shelf-label", "schema/type", "anyOf"),
    ]
    assert "'label' is not valid" in refused.faults[0].message
    assert [fault.rule for fault in read(client, "schema/shelf-label").faults] == ["not-found"]


NEVER_CHECKABLE = {
    "refers to a shape from a type the store does not hold": ("Tool use", {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "bindings": {"type": "array", "items": {"$ref": "kb:schema/nothing#/$defs/binding"}},
        },
    }),
    "names itself as the type it is built on": ("Decision", {
        "allOf": [{"$ref": "kb:schema/decision"}],
        "type": "object",
        "properties": {"title": {"type": "string"}},
    }),
    "declares a link field without saying which kinds it may point at": ("Note", {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "relates_to": {"type": "string", "ref": {"cardinality": "one", "parts": False, "on_delete": "refuse"}},
        },
    }),
}


@when(parsers.re(f"the client defines a type that (?P<fault>{'|'.join(map(re.escape, NEVER_CHECKABLE))})"), target_fixture="attempt")
def _define_a_type_never_checkable(root, client, fault):
    before = everything_under(root)
    title, schema = NEVER_CHECKABLE[fault]
    response = request(client, "schema", title, {"version": 1, "schema": schema}, message=f"Define {title}")
    return {"response": response, "before": before, "after": everything_under(root)}


def _type_rejected(attempt, rule, path, message):
    faults = attempt["response"].faults
    assert (attempt["response"].id, attempt["response"].revision) == ("", 0)
    assert [(fault.path, fault.rule) for fault in faults] == [(path, rule)]
    assert faults[0].message.startswith(message)


@then("the type is rejected because a shape a type refers to must belong to a type the store holds")
def _rejected_for_a_shape_not_held(attempt):
    _type_rejected(attempt, "shape", "schema/properties/bindings/items/$ref",
                   "a shape a type refers to must belong to a type the store holds")


@then("the type is rejected because a type cannot be built on itself")
def _rejected_for_building_on_itself(attempt):
    _type_rejected(attempt, "built-on", "schema/allOf/0/$ref", "a type cannot be built on itself")


@then("the type is rejected because a link field says which kinds it may point at")
def _rejected_for_a_link_without_kinds(attempt):
    _type_rejected(attempt, "targets", "schema/properties/relates_to", "a link field says which kinds it may point at")


@then("nothing is written anywhere in the store")
def _nothing_written(attempt):
    assert attempt["after"] == attempt["before"]
