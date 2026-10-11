"""A type is not defined at the very IRI a link waits on while that IRI belongs to another type
(decision/a-types-place-is-settled-by-what-sits-under-it): the link was written to an artifact of that other type, and
a type there would be none. That holds at landing, in either order. A link waiting on an IRI beside it does not stand
in the way. Through the contract, each store under its own tmp_path; the two changes made at once by two clients on
one machine, landed in the order the test chooses."""
import copy

import pytest

import at_once
from calls import (
    DECISION_TYPE, TAG_TYPE, TYPE_OF_TYPES, TYPES, check, create, creating, define, iri, placeholders, read, request,
    start_a_store, type_iri,
)
from kb import client as kb_client

SECTIONS = [{"title": "Purpose", "body": "Ship what is ready.\n"}, {"title": "Rationale", "body": "Small steps.\n"}]
GHOST, BESIDE = iri("decision", "ghost"), iri("decision", "ghoul")
LINKING = iri("decision", "ship-daily")
GHOST_TYPE = {"version": 1, "schema": TAG_TYPE["schema"]}
# The decision type, but that a decision may supersede a part of another.
DECISIONS = copy.deepcopy(DECISION_TYPE)
DECISIONS["schema"]["properties"]["supersedes"]["ref"]["parts"] = True


def superseding(target):
    """A decision's content as a request carries it, superseding what is named."""
    return {"sections": SECTIONS, "supersedes": target}


@pytest.fixture
def client(root):
    """A store holding the decision type, whose decisions may each supersede another, or a part of one."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISIONS)
    return client


def defining():
    """The define of a type at the IRI a link waits on, as the client sends it."""
    return creating(TYPES, "Ghost", GHOST_TYPE, message="Define Ghost", at=GHOST)


def defined(client):
    return request(client, TYPES, "Ghost", GHOST_TYPE, message="Define Ghost", at=GHOST)


def linked(client, target=GHOST):
    return request(client, "decision", "Ship daily", superseding(target))


def refused_for(refused):
    """The IRIs a refused define names, each fault the define's own and saying they belong to the decision type."""
    assert all((fault.artifact, fault.place, fault.rule) == (GHOST, "", "identity") for fault in refused.faults)
    assert all(repr(type_iri("decision")) in fault.message for fault in refused.faults), refused.faults
    return [fault.message.split("'")[1] for fault in refused.faults]


def waited_on(client):
    return [each.id for each in placeholders(client).placeholders]


def test_a_type_is_not_defined_at_the_iri_a_link_waits_on(client):
    assert not linked(client).faults
    assert refused_for(defined(client)) == [GHOST]
    assert read(client, GHOST).faults and waited_on(client) == [GHOST]
    assert not check(client).violations


def test_a_type_is_not_defined_at_the_iri_a_link_waits_on_a_part_of(client):
    assert not linked(client, GHOST + "#options/go-weekly").faults
    assert refused_for(defined(client)) == [GHOST]
    assert read(client, GHOST).faults and not check(client).violations


def test_a_define_landing_after_a_link_to_its_own_iri_landed_is_refused_naming_it(root, client):
    """The define is drafted while nothing waits on its IRI, and held; the link lands; the define, drafted again while
    it holds the write lock, is refused there."""
    define_it = at_once.OnAThread(root, "Create", defining())

    def first():
        assert not linked(client).faults

    landed = at_once.landed_second(define_it, first)
    assert refused_for(landed) == [GHOST]
    assert read(client, GHOST).faults and waited_on(client) == [GHOST]
    assert not check(client).violations


def test_a_link_landing_after_the_define_of_a_type_at_the_iri_it_waits_on_is_refused(root, client):
    """The link is drafted while the IRI it waits on is held by nothing, and held; the type lands there; the link, read
    again, would land on a type, which its field does not allow."""
    link_it = at_once.OnAThread(root, "Create", creating("decision", "Ship daily", superseding(GHOST)))

    def first():
        assert not defined(client).faults

    landed = at_once.landed_second(link_it, first)
    assert [(fault.artifact, fault.place, fault.rule) for fault in landed.faults] == [(LINKING, "supersedes", "ref")]
    assert read(client, LINKING).faults and not read(client, GHOST).faults
    assert waited_on(client) == [] and not check(client).violations


def test_a_link_waiting_on_an_iri_beside_it_does_not_stand_in_the_way(client):
    assert not linked(client, BESIDE).faults
    assert not defined(client).faults
    assert not read(client, GHOST).faults and waited_on(client) == [BESIDE]
    assert not check(client).violations


def test_a_type_is_defined_at_an_iri_of_the_type_of_types_that_a_link_to_a_type_waits_on(client):
    """A link whose field allows types waits on an IRI under the type of types' own: the type defined there is the
    artifact it waited on."""
    schema = copy.deepcopy(DECISION_TYPE["schema"])
    schema["properties"]["supersedes"]["ref"]["targets"] = [TYPE_OF_TYPES]
    describing, awaited = iri("decision", "describing"), TYPE_OF_TYPES + "/shop/tag"
    assert not request(client, TYPES, "Describing", {"version": 1, "schema": schema}, at=describing).faults
    assert not request(client, describing, "Ship daily", superseding(awaited), at=describing + "/ship-daily").faults
    assert waited_on(client) == [awaited]
    assert not request(client, TYPES, "Tag", GHOST_TYPE, at=awaited).faults
    assert waited_on(client) == [] and not check(client).violations
