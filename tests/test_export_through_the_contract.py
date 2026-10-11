"""Export through the contract, bound to its feature: the steps of the scenarios built so far, each export asked of
the client as any rpc is and its stream read through `calls`."""
import pytest
from pytest_bdd import given, scenarios, then, when

import held
from calls import (DECISION_TYPE, TYPE_OF_TYPES, WORK_ITEM_TYPE, answer, create, define, filed, journal, replace,
                   start_a_store, type_iri)
from kb import client as kb_client
from kb.content import dumps, loads
from kb.contract import kb_pb2

scenarios("export-through-the-contract.feature")

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
REPLACED = [SECTIONS[0], {"title": "Rationale", "body": "Suppliers reprice weekly.\n"}]


@pytest.fixture
def client(root):
    return kb_client.connect(root)


@given("a store holding a type for decisions, a type for work items, two decisions and a work item",
       target_fixture="made")
def _decisions_and_a_work_item(root, client):
    """The store, and the IRI of each artifact made in it that is not a type."""
    start_a_store(root)
    define(client, DECISION_TYPE)
    define(client, WORK_ITEM_TYPE)
    decisions = [create(client, "decision", {"title": title, "sections": SECTIONS}).id
                 for title in ("Price reviews happen weekly", "Prices are reviewed monthly")]
    work_item = create(client, "work-item", {"title": "Move the review to Mondays", "decisions": decisions[:1]})
    return [*decisions, work_item.id]


@given("a store holding a decision, whose replacement is the last entry landed in its history",
       target_fixture="replaced")
def _a_decision_replaced_last(root, client):
    """The decision's IRI, and the entry its replacement landed, the last change made to the store."""
    start_a_store(root)
    define(client, DECISION_TYPE)
    decision = create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS}).id
    assert not replace(client, decision, {"sections": REPLACED}).faults
    made, replacement = journal(client, artifact=decision).entries
    return decision, replacement


@when("the client exports the store", target_fixture="stream")
def _exports(client):
    """The stream as the client is given it, not yet read."""
    return client.Export(kb_pb2.ExportRequest())


@pytest.fixture
def exported(stream):
    """The stream read to its end, once, for every step that reads what it gave."""
    return answer(stream)


@then("the client is given the store's canonical files one at a time")
def _given_the_files_one_at_a_time(exported, made):
    """Each message of the stream gives one file, until the one that ends it; each file's text is canonical, and the
    files are those of the three types' versions and of every artifact made."""
    assert not exported.refused, exported.faults
    assert [message.result.WhichOneof("part") for message in exported.messages] == ["file"] * 6 + ["end"]
    for _, text in exported.files:
        assert dumps(loads(text)) == text
    assert sorted(place for place, _ in exported.files) == sorted(
        [filed(TYPE_OF_TYPES, 1), filed(type_iri("decision"), 1), filed(type_iri("work-item"), 1), *map(filed, made)])


@then("each file comes with the place that follows its artifact's IRI")
def _each_place_follows_its_iri(exported):
    """A type's version is at its type's IRI and its number, any other artifact at its own."""
    for place, text in exported.files:
        artifact = loads(text)
        assert place == filed(artifact["id"], artifact.get("version"))


@then("every file shows the store as it stood at one moment")
def _every_file_shows_the_store(root, exported, made):
    """Nothing has changed since: each artifact's file gives what the store holds of it now."""
    files = {loads(text)["id"]: loads(text) for _, text in exported.files}
    for name in made:
        assert files[name] == held.artifact(root, name)


@then("the client is told the position in the history those files reflect")
def _told_the_position(client, exported, made):
    """The work item was made last: the entry that made it is the last landed."""
    assert exported.complete
    assert exported.position == journal(client, artifact=made[-1]).entries[-1].id


@then("the position the client is told is the position of the history entry the decision's replacement landed")
def _the_position_is_the_replacements(exported, replaced):
    _, replacement = replaced
    assert exported.position == replacement.id


@then("the decision's file shows the decision as that replacement left it")
def _the_file_shows_the_replacement(exported, replaced):
    decision, _ = replaced
    [shown] = [loads(text) for place, text in exported.files if place == filed(decision)]
    assert (shown["revision"], shown["sections"]) == (2, REPLACED)
