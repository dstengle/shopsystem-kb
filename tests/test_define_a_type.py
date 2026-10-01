import re

from pytest_bdd import given, parsers, scenarios, then, when

from calls import DECISION_TYPE, create, define, listing, next_version, read, remove, request, replace
import held
from kb.content import loads

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
    assert (note_type.id, note_type.kind, note_type.title) == ("schema/note", "schema", "Note")
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
    assert [(fault.place, fault.rule) for fault in misfit.faults] == [("bindings/0", "required")]


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
    before = held.holds(root)
    title, schema = NEVER_CHECKABLE[fault]
    response = request(client, "schema", title, {"version": 1, "schema": schema}, message=f"Define {title}")
    return {"response": response, "before": before, "after": held.holds(root)}


def _type_rejected(attempt, rule, path, message):
    faults = attempt["response"].faults
    assert (attempt["response"].id, attempt["response"].revision) == ("", 0)
    assert [(fault.place, fault.rule) for fault in faults] == [(path, rule)]
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


LINK = {"type": "string", "ref": {"targets": ["tag"], "cardinality": "one", "parts": False, "on_delete": "refuse"}}

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
        ("decision/price-reviews-happen-weekly", "about", "ref"),
    ]


@given("a type the store holds at its second version", target_fixture="held")
def _a_type_at_its_second_version(client):
    define(client, DECISION_TYPE)
    next_version(client, "decision", DECISION_TYPE)
    return read(client, "schema/decision", whole=True)


@when("the client changes what that type requires, leaving its version at two", target_fixture="changed")
def _change_the_type_leaving_its_version(client):
    schema = {**DECISION_TYPE["schema"], "required": ["title", "supersedes"]}
    return replace(client, "schema/decision", {"version": 2, "schema": schema}, message="Revise Decision")


@then("the change is rejected because a type's version goes up whenever the type changes")
def _rejected_for_the_version_kept(changed):
    assert [(fault.artifact, fault.place, fault.rule) for fault in changed.faults] == [
        ("schema/decision", "version", "version"),
    ]
    assert changed.faults[0].message.startswith("a type's version goes up whenever the type changes")
    assert changed.revision == 0


@then("the type reads back as it was")
def _the_type_as_it_was(client, held):
    assert read(client, "schema/decision", whole=True) == held


TWO_DECISIONS = ["vote/ship-weekly", "vote/price-monthly"]


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
    return {"response": remove(client, "schema/vote"), "before": before, "after": held.holds(root)}


@then("the removal is rejected because something still points at it, naming each of those two artifacts")
def _rejected_naming_each(client, attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.place, fault.rule) for fault in faults] == [
        (name, "", "on_delete") for name in sorted(TWO_DECISIONS)
    ]
    assert all("'schema/vote'" in fault.message for fault in faults)
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
    assert (defined.id, defined.revision) == ("schema/note", 1)


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
    assert {fault.artifact for fault in refused.faults} == {"schema/note"}
    assert sorted((fault.place, fault.rule) for fault in refused.faults) == sorted(WRITTEN_ORDER)


@then("the faults come in the order the places stand in the type as it reads back, which is the order the client wrote it in")
def _faults_in_the_written_order(attempt):
    assert [fault.place for fault in attempt["response"].faults] == [place for place, _ in WRITTEN_ORDER]


@then("the two faults at the link field come in the alphabetical order of the names of the rules they break")
def _two_faults_at_the_link_field_in_rule_order(attempt):
    assert [fault.rule for fault in attempt["response"].faults if fault.place == "schema/properties/relates_to"] == [
        "ref", "targets",
    ]
