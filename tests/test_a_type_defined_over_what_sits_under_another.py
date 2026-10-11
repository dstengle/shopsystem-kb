"""A type is not defined at an IRI under another type's while an artifact of that other type is held under the new
type's IRI, or a link waits on an IRI there (decision/a-types-place-is-settled-by-what-sits-under-it), and that holds
at landing: a create, or a link, landing under the new type's IRI at the same moment as its define never leaves both
landed. What belongs to a type held nearer does not stand in the way (decision/an-iri-belongs-to-its-nearest-type).
Through the contract, each store under its own tmp_path; the two changes made at once by two clients on one machine,
landed in the order the test chooses."""
import copy

import pytest

import at_once
from calls import (
    DECISION_TYPE, TAG_TYPE, TYPES, check, create, create_many, created, creating, define, iri, placeholders, read,
    remove, request, start_a_store, type_iri,
)
from kb import client as kb_client

SECTIONS = [{"title": "Purpose", "body": "Ship what is ready.\n"}, {"title": "Rationale", "body": "Small steps.\n"}]
MINOR, DEEP = iri("decision", "minor"), iri("decision", "minor/deep")
SITTING, WAITED_ON = iri("decision", "minor/ship-weekly"), iri("decision", "minor/ship-monthly")
LINKING = iri("decision", "ship-daily")
MINOR_TYPE = {"version": 1, "schema": TAG_TYPE["schema"]}


def decision(title, supersedes=None):
    """A decision as a user writes it, title inside, superseding the one named when one is."""
    return {"title": title, **untitled(supersedes)}


def untitled(supersedes=None):
    """A decision's content as a request carries it, its title beside it."""
    return {"sections": SECTIONS, **({"supersedes": supersedes} if supersedes else {})}


@pytest.fixture
def client(root):
    """A store holding the decision type, whose decisions may each supersede another."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    return client


def defining(at=MINOR):
    """The define of a type at an IRI under the decision type's, as the client sends it."""
    return creating(TYPES, "Minor", MINOR_TYPE, message="Define Minor", at=at)


def defined(client, at=MINOR):
    return request(client, TYPES, "Minor", MINOR_TYPE, message="Define Minor", at=at)


def sitting(refused, type_id=MINOR):
    """The IRIs a refused define names as sitting under it, each fault the define's own and saying whose they are."""
    assert all((fault.artifact, fault.place, fault.rule) == (type_id, "", "identity") for fault in refused.faults)
    assert all(repr(type_iri("decision")) in fault.message for fault in refused.faults), refused.faults
    return [fault.message.split("'")[1] for fault in refused.faults]


def test_a_type_with_nothing_under_it_is_defined_under_another_types_iri(client):
    create(client, "decision", decision("Ship daily", iri("decision", "ship-hourly")))
    assert not defined(client).faults
    create(client, MINOR, {"title": "Ship weekly"}, at=SITTING)
    assert not check(client).violations


def test_the_refusal_names_each_iri_once_in_kbs_order_the_held_and_the_waited_on(client):
    create(client, "decision", decision("Ship weekly"), at=SITTING)
    create(client, "decision", decision("Ship daily", WAITED_ON))
    create(client, "decision", decision("Ship hourly", WAITED_ON))
    create(client, "decision", decision("Ship yearly", iri("decision", "minor/a/first")))
    refused = defined(client)
    assert sitting(refused) == [iri("decision", "minor/a/first"), WAITED_ON, SITTING]
    assert read(client, MINOR).faults


def test_what_belongs_to_a_type_held_nearer_does_not_stand_in_the_way(client):
    """A type held at `decision/minor/deep`, one artifact of it and a link waiting on another: all stay that type's
    when a type is defined at `decision/minor`."""
    schema = copy.deepcopy(DECISION_TYPE["schema"])
    schema["properties"]["supersedes"]["ref"]["targets"] = [DEEP]
    assert not request(client, TYPES, "Deep", {"version": 1, "schema": schema}, at=DEEP).faults
    kept, awaited = iri("decision", "minor/deep/kept"), iri("decision", "minor/deep/awaited")
    create(client, DEEP, decision("Kept", awaited), at=kept)
    assert not defined(client).faults
    assert not read(client, kept).faults and not check(client).violations
    assert [each.id for each in placeholders(client).placeholders] == [awaited]


def test_a_define_at_an_iri_already_held_is_refused_for_that_alone(client):
    """A type held at `decision/minor` with a link waiting under it: what waits there is its own, and a second define
    there is refused only as a create at a held IRI is."""
    schema = copy.deepcopy(DECISION_TYPE["schema"])
    schema["properties"]["supersedes"]["ref"]["targets"] = [MINOR]
    assert not request(client, TYPES, "Minor", {"version": 1, "schema": schema}, at=MINOR).faults
    create(client, MINOR, decision("Ship weekly", WAITED_ON), at=SITTING)
    refused = defined(client)
    assert [(fault.artifact, fault.rule) for fault in refused.faults] == [(MINOR, "identity")]
    assert "already holds" in refused.faults[0].message


def test_only_what_sits_under_the_new_types_iri_stands_in_the_way(client):
    create(client, "decision", decision("Ship weekly"), at=iri("decision", "major/ship-weekly"))
    create(client, "decision", decision("Ship daily", iri("decision", "minority")))
    refused = defined(client)
    assert sitting(refused) == [], refused.faults


def test_a_type_is_defined_once_what_sat_under_it_has_gone(client):
    create(client, "decision", decision("Ship weekly"), at=SITTING)
    create(client, "decision", decision("Ship daily", WAITED_ON))
    assert sitting(defined(client)) == [WAITED_ON, SITTING]
    assert not remove(client, SITTING).faults
    assert sitting(defined(client)) == [WAITED_ON]
    assert not remove(client, LINKING).faults
    assert not defined(client).faults


def test_a_set_that_creates_under_the_iri_and_then_defines_the_type_there_is_refused_whole(client):
    refused = create_many(client, [
        created("decision", "Ship weekly", untitled(), at=SITTING),
        created(TYPES, "Minor", MINOR_TYPE, at=MINOR),
    ])
    assert [(fault.artifact, fault.rule) for fault in refused.faults] == [(MINOR, "identity")]
    assert repr(SITTING) in refused.faults[0].message
    assert read(client, SITTING).faults and read(client, MINOR).faults


def test_a_define_landing_after_a_create_landed_under_its_iri_is_refused_naming_it(root, client):
    """The define is drafted while nothing sits under its IRI, and held; the decision lands there; the define, drafted
    again while it holds the write lock, is refused there, before the clock is read a second time."""
    define_it = at_once.OnAThread(root, "Create", defining())
    landed = at_once.landed_second(define_it, lambda: create(client, "decision", decision("Ship weekly"), at=SITTING))
    assert sitting(landed) == [SITTING]
    assert define_it.drafts == 1
    assert read(client, MINOR).faults and not read(client, SITTING).faults
    assert not check(client).violations


def test_a_define_landing_after_a_link_landed_under_its_iri_is_refused_naming_what_it_waits_on(root, client):
    define_it = at_once.OnAThread(root, "Create", defining())
    landed = at_once.landed_second(
        define_it, lambda: create(client, "decision", decision("Ship daily", WAITED_ON)),
    )
    assert sitting(landed) == [WAITED_ON]
    assert read(client, MINOR).faults
    assert [each.id for each in placeholders(client).placeholders] == [WAITED_ON]
    assert not check(client).violations


def test_a_create_landing_after_the_define_of_a_type_above_it_is_refused_as_not_of_its_type(root, client):
    """The decision's create is drafted while its IRI belongs to the decision type, and held; the type between lands;
    the create, drafted again while it holds the write lock, is refused as slice 158 refuses one not under its
    type."""
    create_it = at_once.OnAThread(root, "Create", creating("decision", "Ship weekly", untitled(), at=SITTING))

    def first():
        assert not defined(client).faults

    landed = at_once.landed_second(create_it, first)
    assert [(fault.artifact, fault.place, fault.rule) for fault in landed.faults] == [(SITTING, "", "identity")]
    assert read(client, SITTING).faults and not read(client, MINOR).faults
    assert not check(client).violations


def test_a_link_landing_after_the_define_of_a_type_above_what_it_waits_on_is_refused(root, client):
    """The link is drafted while the IRI it waits on belongs to the decision type, which its field allows, and held;
    the type between lands; the link, read again, would wait on an IRI of a type its field does not allow."""
    linking = creating("decision", "Ship daily", untitled(WAITED_ON))
    create_it = at_once.OnAThread(root, "Create", linking)

    def first():
        assert not defined(client).faults

    landed = at_once.landed_second(create_it, first)
    assert [(fault.artifact, fault.place, fault.rule) for fault in landed.faults] == [(LINKING, "supersedes", "ref")]
    assert read(client, LINKING).faults and not read(client, MINOR).faults
    assert list(placeholders(client).placeholders) == []
    assert not check(client).violations
