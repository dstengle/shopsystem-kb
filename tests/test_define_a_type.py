import copy
import re

from pytest_bdd import given, parsers, scenarios, then, when

from calls import (
    DECISION_TYPE, TAG_TYPE, TYPE_OF_TYPES, WORK_ITEM_TYPE, change_type, check, create, define, iri, kb_ref, listing,
    next_version, read, refs, remove, request, slug, tagged_decision_type, targets, type_iri, version_iri,
)
import held
from kb.content import loads
from kb.metaschema import METASCHEMA

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
                "ref": {"targets": targets("note"), "cardinality": "one", "parts": False, "on_delete": "refuse"},
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
    assert defined.id == type_iri("note")
    note_type = read(client, defined.id)
    assert (note_type.id, note_type.type, note_type.title) == (type_iri("note"), version_iri(TYPE_OF_TYPES), "Note")
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
    assert note.id == iri("note", "first-note")
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
            "bindings": {"type": "array", "items": {"$ref": kb_ref("tool", 1, "#/$defs/binding")}},
        },
        "required": ["title"],
    },
}


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
        "allOf": [{"$ref": kb_ref("base")}],
        "type": "object",
        "properties": {"title": {"type": "string"}, "outcome": {"type": "string"}},
        "required": ["title"],
        "sections": [{"title": "Rationale"}],
        "summary": ["outcome"],
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
    assert [(fault.place, fault.rule) for fault in refused.faults] == [("", "required")]


@then("a decision reads back with its purpose before its rationale")
def _purpose_before_rationale(root, client):
    created = request(client, "decision", "Price reviews happen weekly", {
        "owner": "shopkeeper", "status": "accepted", "sections": BASE_SECTIONS,
    })
    assert not created.faults, created.faults
    on_disk = held.artifact(root, created.id)
    assert [section["title"] for section in on_disk["sections"]] == ["Purpose", "Rationale"]


@when("the client defines a type that does not match the type that describes types", target_fixture="refused")
def _define_a_malformed_type(client):
    return request(client, "schema", "Shelf label", {"version": 1, "schema": {"type": "label"}}, message="Define Shelf label")


@then("the type is rejected because it does not match the type that describes types")
def _rejected_by_the_metaschema(client, refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.place, fault.rule) for fault in refused.faults] == [
        (type_iri("shelf-label"), "schema/type", "anyOf"),
    ]
    assert "'label' is not valid" in refused.faults[0].message
    assert [fault.rule for fault in read(client, type_iri("shelf-label")).faults] == ["not-found"]


def _binding_type(*required):
    """A type that defines the shape of a binding, which must give each of what is named."""
    return {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"], "$defs": {"binding": {
        "type": "object", "properties": {"name": {"type": "string"}, "port": {"type": "integer"}},
        "required": list(required),
    }}}


def _a_binding_type_at_its_second_version(client):
    define(client, {"title": "Tool", "schema": _binding_type("name")})
    changed = change_type(client, "tool", _binding_type("name", "port"))
    assert not changed.faults, changed.faults
    assert loads(read(client, type_iri("tool"), whole=True).content)["version"] == 2


def _referring_to(ref):
    return {"type": "object", "properties": {
        "title": {"type": "string"}, "bindings": {"type": "array", "items": {"$ref": ref}},
    }}


NOT_HELD_AT_ALL, THE_THIRD = kb_ref("nothing", 1, "#/$defs/binding"), kb_ref("tool", 3, "#/$defs/binding")
A_VERSION_HELD = "a shape a type refers to must belong to a type version the store holds"

# What each type that could never check an artifact is: its title, its schema, and the fault it is refused with, the
# place, the rule and what the message says of it.
NEVER_CHECKABLE = {
    "refers to a shape from a version of a type the store does not hold at all": (
        "Tool use", _referring_to(NOT_HELD_AT_ALL),
        ("schema/properties/bindings/items/$ref", "shape", f"{A_VERSION_HELD}; {NOT_HELD_AT_ALL!r} does not"),
    ),
    "refers to a shape from the third version of the binding type": (
        "Tool use", _referring_to(THE_THIRD),
        ("schema/properties/bindings/items/$ref", "shape", f"{A_VERSION_HELD}; {THE_THIRD!r} does not"),
    ),
    "names itself as the type it is built on": (
        "Decision", {"allOf": [{"$ref": kb_ref("decision")}], "type": "object", "properties": {"title": {"type": "string"}}},
        ("schema/allOf/0/$ref", "built-on", "a type cannot be built on itself"),
    ),
    "declares a link field without saying which kinds it may point at": (
        "Note", {"type": "object", "properties": {
            "title": {"type": "string"},
            "relates_to": {"type": "string", "ref": {"cardinality": "one", "parts": False, "on_delete": "refuse"}},
        }},
        ("schema/properties/relates_to", "targets", "a link field says which kinds it may point at; 'relates_to' does not"),
    ),
}


@given("a binding type the store holds at its second version")
def _a_binding_type_held_at_its_second_version(client):
    _a_binding_type_at_its_second_version(client)


@when(parsers.re(f"the client defines a type that (?P<fault>{'|'.join(map(re.escape, NEVER_CHECKABLE))})"), target_fixture="attempt")
def _define_a_type_never_checkable(root, client, fault):
    before = held.holds(root)
    title, schema, _ = NEVER_CHECKABLE[fault]
    response = request(client, "schema", title, {"version": 1, "schema": schema}, message=f"Define {title}")
    return {"response": response, "before": before, "after": held.holds(root)}


def _type_rejected(attempt, rule, path, message):
    faults = attempt["response"].faults
    assert (attempt["response"].id, attempt["response"].revision) == ("", 0)
    assert [(fault.place, fault.rule) for fault in faults] == [(path, rule)]
    assert faults[0].message.startswith(message)


@then("the type is rejected because it could never check an artifact")
def _rejected_as_never_checkable(attempt):
    """With one fault, of one of the three rules kb gives a type that could never check an artifact."""
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert [fault.rule in ("shape", "built-on", "targets") for fault in refused.faults] == [True]


@then(parsers.re(f"the refusal names that the type (?P<fault>{'|'.join(map(re.escape, NEVER_CHECKABLE))})"))
def _the_refusal_names_the_fault(attempt, fault):
    place, rule, message = NEVER_CHECKABLE[fault][2]
    _type_rejected(attempt, rule, place, message)


@then("nothing is written anywhere in the store")
def _nothing_written(attempt):
    assert attempt["after"] == attempt["before"]


LINK = {"type": "string", "ref": {"targets": targets("tag"), "cardinality": "one", "parts": False, "on_delete": "refuse"}}

BASES = {
    "a collection of notes every artifact may carry": {
        "type": "object",
        "parts": {"notes": {"items": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}}},
    },
    "which fields are shown at a glance": {
        "type": "object", "properties": {"owner": {"type": "string"}}, "summary": ["owner"],
    },
    "a link field every artifact may carry": {"type": "object", "properties": {"about": LINK}},
}

RATIONALE = [{"title": "Rationale", "body": "Costs move weekly.\n"}]


@given(parsers.re(f"a base type declaring (?P<declared>{'|'.join(map(re.escape, BASES))})"))
def _a_base_type_declaring(client, declared):
    define(client, {"title": "Base", "version": 1, "schema": BASES[declared]})


@then("a decision of that type can be given notes, and each note is named by the store")
def _given_notes_named_by_the_store(client):
    created = create(client, "decision", {
        "title": "Price reviews happen weekly", "sections": RATIONALE,
        "notes": [{"title": "Check the costs"}, {"title": "Ask the supplier"}],
    })
    notes = loads(read(client, created.id, whole=True).content)["notes"]
    assert [(note["id"], note["title"]) for note in notes] == [
        ("check-the-costs", "Check the costs"), ("ask-the-supplier", "Ask the supplier"),
    ]


@then("reading a decision of that type at a glance shows the base's fields as well as the type's own")
def _the_bases_fields_at_a_glance(client):
    created = create(client, "decision", {
        "title": "Price reviews happen weekly", "owner": "shopkeeper", "outcome": "Weekly", "sections": RATIONALE,
    })
    assert loads(read(client, created.id).content) == {"owner": "shopkeeper", "outcome": "Weekly"}


@then("a decision of that type pointing through that field at a kind the base does not allow is rejected")
def _a_link_through_the_base_refused(client):
    other = create(client, "decision", {"title": "Prices are reviewed monthly", "sections": RATIONALE})
    refused = request(client, "decision", "Price reviews happen weekly", {"about": other.id, "sections": RATIONALE})
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.place, fault.rule) for fault in refused.faults] == [
        (iri("decision", "price-reviews-happen-weekly"), "about", "ref"),
    ]


@given("a type the store holds at its second version", target_fixture="held")
def _a_type_at_its_second_version(client):
    define(client, DECISION_TYPE)
    next_version(client, "decision", DECISION_TYPE)
    return read(client, type_iri("decision"), whole=True)


TWO_DECISIONS = [iri("vote", "ship-weekly"), iri("vote", "price-monthly")]


@given("a type the store holds, and two artifacts of its kind")
def _a_type_and_two_artifacts(client):
    define(client, {"title": "Vote", "version": 1, "schema": {
        "type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"],
    }})
    for title in ("Ship weekly", "Price monthly"):
        create(client, "vote", {"title": title})


@when("the client removes that type", target_fixture="attempt")
def _remove_the_type(root, client):
    before = held.holds(root)
    return {"response": remove(client, type_iri("vote")), "before": before, "after": held.holds(root)}


@then("the removal is rejected because something still points at it, naming each of those two artifacts")
def _rejected_naming_each(client, attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.place, fault.rule) for fault in faults] == [
        (name, "", "on_delete") for name in sorted(TWO_DECISIONS)
    ]
    assert all(repr(type_iri("vote")) in fault.message for fault in faults)
    assert attempt["after"] == attempt["before"]
    assert list(listing(client, "vote", ids_only=True).ids) == sorted(TWO_DECISIONS)


MISPLACED = {
    "declares a link field inside a field's own nested schema": (
        {"type": "object", "properties": {"title": {"type": "string"}, "about": {
            "type": "object", "properties": {"label": {"type": "string"}, "link": LINK},
        }}},
        "schema/properties/about/properties/link/ref",
    ),
    "declares a collection inside a field's own nested schema": (
        {"type": "object", "properties": {"title": {"type": "string"}, "about": {
            "type": "object", "properties": {"label": {"type": "string"}},
            "parts": {"notes": {"items": {"type": "object", "properties": {"title": {"type": "string"}}}}},
        }}},
        "schema/properties/about/parts",
    ),
    "declares required sections inside a collection's items": (
        {"type": "object", "properties": {"title": {"type": "string"}}, "parts": {"notes": {"items": {
            "type": "object", "properties": {"title": {"type": "string"}}, "sections": [{"title": "Context"}],
        }}}},
        "schema/parts/notes/items/sections",
    ),
    "declares the fields shown at a glance inside a field's own nested schema": (
        {"type": "object", "properties": {"title": {"type": "string"}, "about": {
            "type": "object", "properties": {"label": {"type": "string"}}, "summary": ["label"],
        }}},
        "schema/properties/about/summary",
    ),
}


@when(parsers.re(f"the client defines a type that (?P<misplaced>{'|'.join(map(re.escape, MISPLACED))})"), target_fixture="attempt")
def _define_a_type_misplacing(root, client, misplaced):
    before = held.holds(root)
    schema, place = MISPLACED[misplaced]
    response = request(client, "schema", "Note", {"version": 1, "schema": schema}, message="Define Note")
    return {"response": response, "before": before, "after": held.holds(root), "place": place}


@then("the type is rejected because kb does not read a link field there")
def _rejected_for_a_misplaced_link(attempt):
    _type_rejected(attempt, "ref", attempt["place"], "kb does not read a link field there")


@then("the type is rejected because kb does not read them there")
def _rejected_for_a_misplaced_keyword(attempt):
    _type_rejected(attempt, "placement", attempt["place"], "kb does not read")


@then("the refusal names the place")
def _the_refusal_names_the_place(attempt):
    assert [fault.place for fault in attempt["response"].faults] == [attempt["place"]]


def _ref_without(key):
    return {name: value for name, value in LINK["ref"].items() if name != key}


FLAWED_LINKS = {
    "that does not say whether it points at one artifact or several": _ref_without("cardinality"),
    "that does not say whether it may point into a part": _ref_without("parts"),
    "that does not say what a removal does": _ref_without("on_delete"),
    "whose removal rule is cascade": {**LINK["ref"], "on_delete": "cascade"},
    "that says it points at two artifacts": {**LINK["ref"], "cardinality": "two"},
}


@when(parsers.re(f"the client defines a type with a link field (?P<flaw>{'|'.join(map(re.escape, FLAWED_LINKS))})"), target_fixture="attempt")
def _define_a_type_with_a_flawed_link(root, client, flaw):
    before = held.holds(root)
    schema = {"type": "object", "properties": {
        "title": {"type": "string"}, "relates_to": {"type": "string", "ref": FLAWED_LINKS[flaw]},
    }}
    response = request(client, "schema", "Note", {"version": 1, "schema": schema}, message="Define Note")
    return {"response": response, "before": before, "after": held.holds(root), "place": "schema/properties/relates_to"}


@then(
    "the type is rejected because a link field says which kinds it may point at, whether it points at one artifact "
    "or several, whether it may point into a part and what a removal does"
)
def _rejected_for_a_link_left_incomplete(attempt):
    _type_rejected(attempt, "ref", attempt["place"], (
        "a link field says which kinds it may point at, whether it points at one artifact or several, whether it may "
        "point into a part and what a removal does"
    ))


@then("the type is rejected because refuse is the one removal rule kb knows")
def _rejected_for_a_removal_rule(attempt):
    _type_rejected(attempt, "ref", attempt["place"], "refuse is the one removal rule kb knows")


@then("the type is rejected because a link field points at one artifact or several")
def _rejected_for_a_reach(attempt):
    _type_rejected(attempt, "ref", attempt["place"], "a link field points at one artifact or several")


KEYWORDS = {
    "enum": {"kind": {"type": "string", "enum": ["ref", "parts", "sections", "summary"]}},
    "pattern": {"code": {"type": "string", "pattern": "^[a-z]+$"}},
    "format": {"due": {"type": "string", "format": "date"}},
}


@when(parsers.parse("the client defines a type that uses {keyword} inside a field's own nested schema"), target_fixture="defined")
def _define_a_type_using(client, keyword):
    extra = {"type": "object", "properties": KEYWORDS[keyword]}
    schema = {**NOTE_TYPE["schema"], "properties": {**NOTE_TYPE["schema"]["properties"], "extra": extra}}
    return request(client, "schema", "Note", {"version": 1, "schema": schema}, message="Define Note")


@then("the type is accepted")
def _the_type_is_accepted(defined):
    assert not defined.faults, defined.faults
    assert defined.revision == 1


@when(
    parsers.re(r'the client defines a type, giving it the IRI "(?P<at>[^"]+)"(?:, which does not sit under "[^"]+")?'),
    target_fixture="defined",
)
def _define_a_type_at(client, at):
    return request(client, "schema", DECISION_TYPE["title"], {key: DECISION_TYPE[key] for key in ("version", "schema")},
                   message="Define Decision", at=at)


@then(parsers.parse('the type is held at "{at}"'))
def _type_held_at(client, at):
    held_type = read(client, at)
    assert not held_type.faults, held_type.faults
    assert (held_type.id, held_type.type) == (at, version_iri(TYPE_OF_TYPES))


@then(parsers.parse('its version is held at "{at}", "@" and the version\'s number'))
def _version_held_at(client, at):
    """The version is the number the type stands at; a create naming that version's IRI is refused for nothing but
    the title it leaves out, never for its version, and writes nothing."""
    number = loads(read(client, at, whole=True).content)["version"]
    probe = request(client, at, "", {}, at=f"{at}/probe", version=number)
    assert [fault.rule for fault in probe.faults] == ["title"]


@then(parsers.parse('an artifact created of that type has an IRI under "{at}"'))
def _artifact_under(client, at):
    made = request(client, at, "Price reviews happen weekly", {"sections": [
        {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
        {"title": "Rationale", "body": "Costs move weekly.\n"},
    ]}, version=1)
    assert not made.faults, made.faults
    assert made.id.startswith(at + "/")


@when(parsers.parse('the client reads "{at}"'), target_fixture="read_back")
def _client_reads(client, at):
    return read(client, at, whole=True)


@then("it reads back the type that describes types")
def _the_type_of_types(read_back):
    assert (read_back.id, read_back.type, read_back.title) == (TYPE_OF_TYPES, version_iri(TYPE_OF_TYPES), METASCHEMA["title"])
    assert loads(read_back.content) == {key: value for key, value in METASCHEMA.items() if key != "title"}


WRITTEN_ORDER = [
    ("schema/properties/about/sections", "placement"),
    ("schema/properties/relates_to", "ref"),
    ("schema/properties/relates_to", "targets"),
    ("schema/parts/attachments/items/sections", "placement"),
]


@when(
    "the client defines a type where one field breaks two of kb's rules for a link field, a field's nested schema "
    "declares required sections, and a collection's items declare required sections",
    target_fixture="attempt",
)
def _define_a_type_with_several_faults(root, client):
    """Written the field with nested sections first, then the link field, the collection last: the order a walk of its
    keywords finds them in too, so this scenario alone does not pin the order; tests/test_the_order_of_faults.py
    does, with a type whose faults are found in an order other than the one it is written in."""
    before = held.holds(root)
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "about": {"type": "object", "sections": [{"title": "Context"}]},
            "relates_to": {"type": "string", "ref": {"cardinality": "one", "parts": False}},
        },
        "parts": {"attachments": {"items": {"type": "object", "sections": [{"title": "Outcome"}]}}},
    }
    response = request(client, "schema", "Note", {"version": 1, "schema": schema}, message="Define Note")
    return {"response": response, "before": before, "after": held.holds(root)}


@then("the type is rejected with every fault, each naming the place")
def _rejected_with_every_fault(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert {fault.artifact for fault in refused.faults} == {type_iri("note")}
    assert sorted((fault.place, fault.rule) for fault in refused.faults) == sorted(WRITTEN_ORDER)


@then("the faults come in the order the places stand in the type as it reads back, which is the order the client wrote it in")
def _faults_in_the_written_order(attempt):
    assert [fault.place for fault in attempt["response"].faults] == [place for place, _ in WRITTEN_ORDER]


@then("the two faults at the link field come in the alphabetical order of the names of the rules they break")
def _two_faults_at_the_link_field_in_rule_order(attempt):
    assert [fault.rule for fault in attempt["response"].faults if fault.place == "schema/properties/relates_to"] == [
        "ref", "targets",
    ]


def _with(schema, field, required=False):
    """A type's schema with one more field, required when it is said to be."""
    changed = copy.deepcopy(schema)
    changed["properties"][field] = {"type": "string"}
    if required:
        changed["required"] = [*changed["required"], field]
    return changed


AS_DEFINED = DECISION_TYPE["schema"]
AS_FIRST_CHANGED = _with(AS_DEFINED, "owner")
AS_CHANGED = _with(AS_FIRST_CHANGED, "status", required=True)


def _reads_as_made(client, at, number, schema):
    """The version of the type at an IRI with the number given reads at its own IRI with the schema, the number, the
    revision and the title it was made with."""
    made = read(client, f"{at}@{number}", whole=True)
    assert not made.faults, made.faults
    assert (made.id, made.type, made.title, made.revision) == (
        f"{at}@{number}", version_iri(TYPE_OF_TYPES), DECISION_TYPE["title"], number,
    )
    assert loads(made.content) == {"version": number, "schema": schema}


@given(parsers.parse('a type the store holds at "{at}", changed once since it was defined'), target_fixture="at")
def _a_type_changed_once(client, at):
    defined = request(client, "schema", DECISION_TYPE["title"], {"schema": AS_DEFINED}, message="Define Decision", at=at)
    assert not defined.faults, defined.faults
    changed = change_type(client, at, AS_FIRST_CHANGED)
    assert not changed.faults, changed.faults
    return at


@when("the client changes what that type requires", target_fixture="changed")
def _change_what_the_type_requires(client, at):
    return change_type(client, at, AS_CHANGED)


@then(parsers.parse('the change makes a new version at "{at}", "@" and the new version\'s number'))
def _a_new_version_at(client, changed, at):
    assert not changed.faults, changed.faults
    number = loads(read(client, at, whole=True).content)["version"]
    assert number == 3
    _reads_as_made(client, at, number, AS_CHANGED)


@then("the version the type was defined with reads back as it was made")
def _the_defined_version_as_made(client, at):
    _reads_as_made(client, at, 1, AS_DEFINED)


@then("the version its first change made reads back as it was made")
def _the_first_changes_version_as_made(client, at):
    _reads_as_made(client, at, 2, AS_FIRST_CHANGED)


@when("the client changes that type", target_fixture="changed")
def _change_that_type(client):
    """The type as it stands, one more field in its schema and no number sent."""
    standing = loads(read(client, type_iri("decision"), whole=True).content)["schema"]
    return change_type(client, "decision", _with(standing, "reviewer"))


@then("the new version is the type's third")
def _the_new_version_is_the_third(client, changed):
    assert not changed.faults, changed.faults
    assert loads(read(client, type_iri("decision"), whole=True).content)["version"] == 3
    _reads_as_made(client, type_iri("decision"), 3, _with(AS_DEFINED, "reviewer"))
    assert [fault.rule for fault in read(client, version_iri("decision", 4)).faults] == ["not-found"]


def _a_decision_of_the_first_version(client):
    define(client, DECISION_TYPE)
    return create(client, "decision", {"title": "Price reviews happen weekly", "sections": BASE_SECTIONS}).id


@given("a type the store holds at its first version, and an artifact conforming to that version", target_fixture="conforming")
def _a_type_and_an_artifact_of_its_first_version(client):
    return _a_decision_of_the_first_version(client)


@then("the store still holds the type's first version")
def _the_first_version_still_held(client):
    _reads_as_made(client, type_iri("decision"), 1, AS_DEFINED)


@then("the artifact still conforms to the type's first version")
def _the_artifact_still_of_the_first_version(client, changed, conforming):
    assert not changed.faults, changed.faults
    assert read(client, conforming).type == version_iri("decision", 1)


@given(
    "a type the store holds at its second version, and the only artifact conforming to its first version",
    target_fixture="conforming",
)
def _a_type_moved_on_from_its_only_artifact(client):
    conforming = _a_decision_of_the_first_version(client)
    changed = change_type(client, "decision", AS_FIRST_CHANGED)
    assert not changed.faults, changed.faults
    return conforming


@when("the client removes that artifact")
def _remove_that_artifact(client, conforming):
    removed = remove(client, conforming)
    assert not removed.faults, removed.faults
    assert [fault.rule for fault in read(client, conforming).faults] == ["not-found"]


TAG_LINK = {"targets": targets("tag"), "cardinality": "one", "parts": False, "on_delete": "refuse"}
NOTE_LINK = {**TAG_LINK, "targets": targets("note")}
NOTE_LINKING_A_TAG = {"type": "object", "required": ["title"], "properties": {
    "title": {"type": "string"}, "tag": {"type": "string", "ref": TAG_LINK}, "reference": {"type": "string"},
}}
NOTE_REFERRING = {"type": "object", "required": ["title"], "properties": {
    "title": {"type": "string"}, "tag": {"type": "string"}, "reference": {"type": "string", "ref": NOTE_LINK},
}}
THE_TAG, THE_NOTE = iri("tag", "pricing"), iri("note", "weekly")


@given("a note type the store holds at its first version, whose notes link to a tag and hold a reference as plain text")
def _a_note_type_linking_a_tag(client):
    define(client, TAG_TYPE)
    define(client, {"title": "Note", "schema": NOTE_LINKING_A_TAG})


@given("a tag, and a note conforming to that version that links to the tag and holds a reference")
def _a_tag_and_a_note_linking_it(client):
    """The reference names the note itself, which the changed type would make a link to it."""
    create(client, "tag", {"title": "Pricing"})
    create(client, "note", {"title": "Weekly", "tag": THE_TAG, "reference": THE_NOTE})


@when("the client changes the note type so that notes no longer link to a tag and their reference is a link")
def _change_the_note_type_to_refer(client):
    changed = change_type(client, "note", NOTE_REFERRING)
    assert not changed.faults, changed.faults


@then("removing the tag is rejected because something still points at it, naming the note")
def _removing_the_tag_rejected(client):
    refused = remove(client, THE_TAG)
    assert [(fault.artifact, fault.rule) for fault in refused.faults] == [(THE_NOTE, "on_delete")]
    assert not read(client, THE_TAG).faults


@then("the note's reference is not a link")
def _the_reference_is_not_a_link(client):
    assert list(read(client, THE_NOTE).inbound) == []
    assert "reference" not in [stub.field for stub in read(client, THE_NOTE).references]


OWNER_REQUIRED = _with(AS_DEFINED, "owner", required=True)


@given(
    "a decision type the store holds at its first version, which does not require an owner, and a decision with no owner",
    target_fixture="conforming",
)
def _a_decision_with_no_owner(client):
    return _a_decision_of_the_first_version(client)


@when("the client changes the decision type to require an owner", target_fixture="changed")
def _change_the_type_to_require_an_owner(client):
    return change_type(client, "decision", OWNER_REQUIRED)


@then("the change is accepted as the type's second version")
def _accepted_as_the_second_version(client, changed):
    assert not changed.faults, changed.faults
    _reads_as_made(client, type_iri("decision"), 2, OWNER_REQUIRED)


@then("the decision still conforms to the type's first version")
def _the_decision_still_of_the_first_version(client, conforming):
    assert read(client, conforming).type == version_iri("decision", 1)


@then("checking the store lists the decision as behind its type, not as a violation")
def _check_lists_it_as_behind(client, conforming):
    checked = check(client)
    assert not checked.faults, checked.faults
    assert list(checked.violations) == []
    assert [(entry.artifact, entry.schema_version, entry.current) for entry in checked.stale] == [(conforming, 1, 2)]


OF_THE_FIRST, OF_THE_SECOND = iri("decision", "price-reviews-happen-weekly"), iri("decision", "stock-is-counted-monthly")


@given(
    "a decision type the store holds at its second version, a decision conforming to its first version and a decision "
    "conforming to its second"
)
def _a_decision_of_each_version(client):
    _a_decision_of_the_first_version(client)
    changed = change_type(client, "decision", AS_FIRST_CHANGED)
    assert not changed.faults, changed.faults
    made = request(client, "decision", "Stock is counted monthly", {"owner": "shopkeeper", "sections": BASE_SECTIONS}, version=2)
    assert not made.faults, made.faults
    assert [read(client, each).type for each in (OF_THE_FIRST, OF_THE_SECOND)] == [
        version_iri("decision", 1), version_iri("decision", 2),
    ]


@given("a type whose link field names the kinds it may point at by the decision type's IRI")
def _a_type_linking_decisions_by_their_types_iri(client):
    assert WORK_ITEM_TYPE["schema"]["properties"]["decisions"]["ref"]["targets"] == [type_iri("decision")]
    define(client, WORK_ITEM_TYPE)


@when("the client creates an artifact of that type pointing through that field at both decisions", target_fixture="pointing")
def _create_pointing_at_both(client):
    return request(client, "work-item", "Review the prices", {"decisions": [OF_THE_FIRST, OF_THE_SECOND]})


@then("the artifact is created")
def _the_artifact_is_created(pointing):
    assert not pointing.faults, pointing.faults
    assert (pointing.id, pointing.revision) == (iri("work-item", "review-the-prices"), 1)


@then("it points at both decisions")
def _it_points_at_both(client, pointing):
    reached = refs(client, pointing.id, 1, via="decisions").reached
    assert [each.stub.id for each in reached] == [OF_THE_FIRST, OF_THE_SECOND]
    for each in (OF_THE_FIRST, OF_THE_SECOND):
        assert [fault.artifact for fault in remove(client, each).faults] == [pointing.id]


@given(
    "a type that defines the shape of a binding, whose first version requires a binding to give a name, and whose "
    "second version requires a name and a port"
)
def _a_binding_type_changed_to_require_a_port(client):
    _a_binding_type_at_its_second_version(client)


@when("the client defines a second type that refers to the binding's shape, naming the first version of that type by its IRI")
def _define_a_type_reading_the_first_version(client):
    assert TOOL_USE_TYPE["schema"]["properties"]["bindings"]["items"] == {"$ref": f"kb:{type_iri('tool')}@1#/$defs/binding"}
    define(client, TOOL_USE_TYPE)


@then("an artifact of the second type whose binding gives a name and no port is accepted")
def _a_binding_with_no_port_accepted(client):
    fits = request(client, "tool-use", "Weigh the flour", {"bindings": [{"name": "scale"}]})
    assert not fits.faults, fits.faults
    assert fits.revision == 1


@then("an artifact of the second type whose binding gives no name is rejected because it does not fit its type")
def _a_binding_with_no_name_rejected(client):
    misfit = request(client, "tool-use", "Weigh the sugar", {"bindings": [{"port": 8080}]})
    assert (misfit.id, misfit.revision) == ("", 0)
    assert [(fault.place, fault.rule) for fault in misfit.faults] == [("bindings/0", "required")]
    assert "'name' is a required property" in misfit.faults[0].message


# What the second type's first version is, by how it reads the first type's first version, and the first type's short
# name with the schema it was defined with and the one it was then changed to.
READ_BY_ANOTHER = {
    "refers to a shape the first type's first version defines": (
        TOOL_USE_TYPE, "tool", TOOL_TYPE["schema"], _with(TOOL_TYPE["schema"], "maker"),
    ),
    "is built on the first type's first version": (
        DECISION_ON_BASE_TYPE, "base", BASE_TYPE["schema"], _with(BASE_TYPE["schema"], "reviewer"),
    ),
}


@given(
    parsers.re(
        "a type the store holds, with no artifacts of its kind, and a second type whose first version "
        f"(?P<reads_it>{'|'.join(map(re.escape, READ_BY_ANOTHER))})"
    ),
    target_fixture="read_by_another",
)
def _a_type_another_types_first_version_reads(client, reads_it):
    """The first type stands at its second version, so that it has versions to keep; the second type reads its first."""
    second, first, defined, changed = READ_BY_ANOTHER[reads_it]
    define(client, {"title": first.title(), "schema": defined})
    assert not change_type(client, first, changed).faults
    define(client, second)
    assert list(listing(client, first, ids_only=True).ids) == []
    return {"first": type_iri(first), "second": type_iri(slug(second["title"])), "versions": [defined, changed]}


@when("the client removes the first type", target_fixture="attempt")
def _remove_the_first_type(root, client, read_by_another):
    before = held.holds(root)
    return {"response": remove(client, read_by_another["first"]), "before": before, "after": held.holds(root)}


@then("the removal is rejected because something still points at it, naming the second type")
def _rejected_naming_the_second_type(attempt, read_by_another):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.place, fault.rule) for fault in faults] == [(read_by_another["second"], "", "on_delete")]
    assert repr(read_by_another["first"]) in faults[0].message
    assert attempt["after"] == attempt["before"]


@then("the store still holds the first type and its versions")
def _the_first_type_and_its_versions_still_held(client, read_by_another):
    first = read_by_another["first"]
    standing = read(client, first, whole=True)
    assert not standing.faults, standing.faults
    assert loads(standing.content) == {"version": 2, "schema": read_by_another["versions"][1]}
    for number, schema in enumerate(read_by_another["versions"], start=1):
        made = read(client, f"{first}@{number}", whole=True)
        assert not made.faults, made.faults
        assert loads(made.content) == {"version": number, "schema": schema}


WAITED_ON, WAITING = iri("tag", "pricing"), iri("decision", "ship-weekly")


@given("a tag type the store holds, with no artifacts of its kind, and a decision that links to a tag the store does not hold")
def _a_tag_type_a_link_waits_under(client):
    define(client, TAG_TYPE)
    define(client, tagged_decision_type())
    create(client, "decision", {"title": "Ship weekly", "tags": [WAITED_ON], "sections": [
        {"title": "Purpose", "body": "Ship what is ready.\n"}, {"title": "Rationale", "body": "Small steps.\n"},
    ]})
    assert list(listing(client, "tag", ids_only=True).ids) == []
    assert read(client, WAITED_ON).faults


@when("the client removes the tag type", target_fixture="attempt")
def _remove_the_tag_type(root, client):
    before = held.holds(root)
    return {"response": remove(client, type_iri("tag")), "before": before, "after": held.holds(root)}


@then("the removal is rejected because something still points at it, naming the decision")
def _rejected_naming_the_decision(attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.place, fault.rule) for fault in faults] == [(WAITING, "", "on_delete")]
    assert repr(type_iri("tag")) in faults[0].message
    assert attempt["after"] == attempt["before"]


@then("the store still holds the tag type")
def _the_tag_type_still_held(client):
    standing = read(client, type_iri("tag"), whole=True)
    assert not standing.faults, standing.faults
