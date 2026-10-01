"""Where kb reads its own keywords in a type, beyond the scenarios: kb's keyword names as data are never refused; a
keyword under a top `allOf` member is read, one under any other branch refused at the keyword's place; the fields
shown at a glance are refused at the top of a collection's items; collections at depth are read, an ordinary array's
`items` is not a collection's; a `ref` both misplaced and malformed is refused for its place alone. Through the
contract, each store under its own tmp_path."""
import pytest

from calls import define, request, start_a_store
from kb import client as kb_client

LINK = {"type": "string", "ref": {"targets": ["tag"], "cardinality": "one", "parts": False, "on_delete": "refuse"}}
TITLE = {"title": {"type": "string"}}


@pytest.fixture
def client(root):
    connected = kb_client.connect(root)
    start_a_store(root)
    return connected


def _define(client, schema, title="Note"):
    return request(client, "schema", title, {"version": 1, "schema": schema}, message=f"Define {title}")


def _faults(response):
    return [(fault.place, fault.rule) for fault in response.faults]


def _object(properties, **rest):
    return {"type": "object", "properties": {**TITLE, **properties}, **rest}


def test_kbs_keyword_names_as_data_are_never_refused(client):
    nested = {"type": "object", "properties": {
        "ref": {"type": "string"}, "parts": {"type": "string"}, "sections": {"type": "string"},
        "summary": {"type": "string", "enum": ["ref", "parts"]},
        "shape": {"type": "object", "default": {"ref": {"targets": ["tag"]}}, "examples": [{"parts": {}, "sections": []}]},
    }}
    schema = _object(
        {"about": nested, "link": {**LINK, "ref": {**LINK["ref"], "parts": True}}},
        sections=[{"title": "Context", "sections": [{"title": "Background"}]}],
        required=["title"],
    )
    assert _faults(_define(client, schema)) == []
    made = request(client, "note", "First", {
        "about": {"ref": "a", "parts": "b", "sections": "c", "summary": "ref", "shape": {"ref": {"targets": []}}},
        "sections": [{"title": "Context", "body": "Why.\n", "sections": [{"title": "Background", "body": "Then.\n"}]}],
    })
    assert not made.faults, made.faults


READ_UNDER_A_TOP_ALL_OF = {
    "a link field": ({"allOf": [_object({"about": LINK})]}, {"about": "tag/nothing"}, "about"),
    "a collection's link field": (
        {"allOf": [{"type": "object", "properties": TITLE, "parts": {"a": {"items": _object({"about": LINK})}}}]},
        {"a": [{"title": "One", "about": "tag/nothing"}]}, "a/0/about",
    ),
    "a collection's items' own allOf": (
        _object({}, parts={"a": {"items": {"allOf": [_object({"about": LINK})]}}}),
        {"a": [{"title": "One", "about": "tag/nothing"}]}, "a/0/about",
    ),
    "two levels of collections": (
        _object({}, parts={"a": {"items": _object({}, parts={"b": {"items": _object({"about": LINK})}})}}),
        {"a": [{"title": "One", "b": [{"title": "Two", "about": "tag/nothing"}]}]}, "a/0/b/0/about",
    ),
}


@pytest.mark.parametrize("where", READ_UNDER_A_TOP_ALL_OF)
def test_a_link_field_where_kb_reads_one_is_accepted_and_read(client, where):
    schema, content, place = READ_UNDER_A_TOP_ALL_OF[where]
    assert _faults(_define(client, schema)) == []
    refused = request(client, "note", "First", content)
    assert _faults(refused) == [(place, "ref")]


def test_collections_and_glance_fields_under_a_top_all_of_are_accepted(client):
    schema = {"allOf": [
        {"type": "object", "properties": {"owner": {"type": "string"}}, "summary": ["owner"]},
        {"type": "object", "parts": {"notes": {"items": _object({})}}, "sections": [{"title": "Context"}]},
    ], "properties": TITLE}
    assert _faults(_define(client, schema)) == []


def test_a_collections_items_given_by_a_whole_type_are_not_walked_into(client):
    define(client, {"title": "Checklist", "version": 1, "schema": _object({}, sections=[{"title": "Steps"}])})
    assert _faults(_define(client, _object({}, parts={"lists": {"items": {"$ref": "kb:schema/checklist"}}}))) == []


MISPLACED = {
    "oneOf": ({"oneOf": [_object({"about": LINK})]}, "schema/oneOf/0/properties/about/ref", "ref"),
    "anyOf": ({"anyOf": [_object({}, parts={"a": {"items": {}}})]}, "schema/anyOf/0/parts", "placement"),
    "not": ({"not": {"summary": ["title"]}}, "schema/not/summary", "placement"),
    "if": ({"if": {"sections": []}}, "schema/if/sections", "placement"),
    "then": ({"then": _object({"about": LINK})}, "schema/then/properties/about/ref", "ref"),
    "else": ({"else": {"parts": {}}}, "schema/else/parts", "placement"),
    "a nested field's allOf": (
        _object({"about": {"allOf": [_object({"link": LINK})]}}), "schema/properties/about/allOf/0/properties/link/ref",
        "ref",
    ),
    "a field's own allOf member": (
        _object({"about": {"allOf": [{"summary": ["title"]}]}}), "schema/properties/about/allOf/0/summary", "placement",
    ),
    "a named shape of the type": (
        {**_object({}), "$defs": {"binding": _object({"d": LINK})}}, "schema/$defs/binding/properties/d/ref", "ref",
    ),
    "a named shape of a nested field": (
        _object({"about": {"$defs": {"binding": _object({"d": LINK})}}}),
        "schema/properties/about/$defs/binding/properties/d/ref", "ref",
    ),
    "a named shape of a collection's items": (
        _object({}, parts={"a": {"items": {**_object({}), "$defs": {"binding": _object({"d": LINK})}}}}),
        "schema/parts/a/items/$defs/binding/properties/d/ref", "ref",
    ),
    "sections in a collection's items' allOf": (
        _object({}, parts={"a": {"items": {"allOf": [{"sections": [{"title": "Context"}]}]}}}),
        "schema/parts/a/items/allOf/0/sections", "placement",
    ),
    "sections two levels of collections down": (
        _object({}, parts={"a": {"items": _object({}, parts={"b": {"items": {"sections": []}}})}}),
        "schema/parts/a/items/parts/b/items/sections", "placement",
    ),
    "an ordinary array field's items": (
        _object({"tags": {"type": "array", "items": {"type": "string", "ref": LINK["ref"]}}}),
        "schema/properties/tags/items/ref", "ref",
    ),
    "the top of the schema itself": ({**_object({}), "ref": LINK["ref"]}, "schema/ref", "ref"),
    "glance fields at the top of a collection's items": (
        _object({}, parts={"a": {"items": _object({}, summary=["title"])}}), "schema/parts/a/items/summary",
        "placement",
    ),
    "glance fields in a collection's items' allOf": (
        _object({}, parts={"a": {"items": {"allOf": [_object({}, summary=["title"])]}}}),
        "schema/parts/a/items/allOf/0/summary", "placement",
    ),
}


@pytest.mark.parametrize("where", MISPLACED)
def test_a_keyword_where_kb_does_not_read_it_is_refused_at_its_place(client, where):
    schema, place, rule = MISPLACED[where]
    refused = _define(client, schema)
    assert (refused.id, refused.revision) == ("", 0)
    assert _faults(refused) == [(place, rule)]


def test_a_misplaced_and_malformed_link_is_refused_for_its_place_alone(client):
    nested = _object({"about": _object({"link": {"type": "string", "ref": {"cardinality": "two"}}})})
    assert _faults(_define(client, nested)) == [("schema/properties/about/properties/link/ref", "ref")]


def test_a_placed_link_without_kinds_is_refused_for_its_kinds_alone(client):
    ref = {key: value for key, value in LINK["ref"].items() if key != "targets"}
    assert _faults(_define(client, _object({"about": {"type": "string", "ref": ref}}))) == [
        ("schema/properties/about", "targets"),
    ]


def test_a_placed_link_without_kinds_or_reach_breaks_two_rules_at_the_field(client):
    ref = {"parts": False, "on_delete": "refuse"}
    assert _faults(_define(client, _object({"about": {"type": "string", "ref": ref}}))) == [
        ("schema/properties/about", "ref"), ("schema/properties/about", "targets"),
    ]
