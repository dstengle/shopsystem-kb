from pytest_bdd import given, parsers, scenario, then, when

from calls import (
    CLIENT, TAG_TYPE, answer, create, creating, define, journal, listing, read, remove, removing, request,
    tagged_decision_type,
)
import at_once
import held
from kb import client as kb_client
from kb.contract import kb_pb2


@scenario("change-the-store.feature", "The client removes an artifact nothing points at")
def test_the_client_removes_an_artifact_nothing_points_at():
    pass


@scenario("change-the-store.feature", "A removal something points at is refused")
def test_a_removal_something_points_at_is_refused():
    pass


@scenario("change-the-store.feature", "A link from inside a part blocks a removal like any other")
def test_a_link_from_inside_a_part_blocks_a_removal_like_any_other():
    pass


@scenario("change-the-store.feature", "A removal and a new link to the same artifact made at once never both land")
def test_a_removal_and_a_new_link_to_the_same_artifact_made_at_once_never_both_land():
    pass


@scenario("name-artifacts-and-items.feature", "A name is free again once what held it has been removed")
def test_a_name_is_free_again_once_what_held_it_has_been_removed():
    pass


@scenario("name-what-is-asked-for.feature", "Removing something the store does not hold is refused")
def test_removing_something_the_store_does_not_hold_is_refused():
    pass


LOOSE = "tag/clearance"
HELD = "tag/pricing"
DECISION = "decision/price-reviews-happen-weekly"


@given("a store holding a tag nothing points at", target_fixture="client")
def _store_with_a_loose_tag(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, TAG_TYPE)
    define(client, tagged_decision_type())
    create(client, "tag", {"title": "Clearance"})
    return client


@given("a tag a decision points at")
def _a_tag_in_use(client):
    create(client, "tag", {"title": "Pricing"})
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "tags": [HELD],
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    })


@when("the client removes the tag nothing points at, saying which role and why", target_fixture="removed")
def _remove_the_loose_tag(client):
    response = remove(client, LOOSE, message="Nothing is on clearance")
    assert not response.faults, response.faults
    return response


@then("the store no longer holds it")
def _no_longer_held(client, root):
    assert [fault.rule for fault in read(client, LOOSE).faults] == ["not-found"]
    assert not held.holds_artifact(root, LOOSE)
    assert list(listing(client, "tag", ids_only=True).ids) == [HELD]


@then("the removal is recorded like any other change")
def _recorded(client, removed):
    entry = journal(client, LOOSE).entries[-1]
    assert (entry.op, entry.revision, entry.actor.role, entry.message, entry.batch) == (
        "delete", 2, "client", "Nothing is on clearance", entry.id,
    )
    assert removed.revision == 2


@when("the client removes the tag the decision points at, saying which role and why", target_fixture="attempt")
def _remove_the_held_tag(root, client):
    before = held.holds(root)
    response = remove(client, HELD, message="Pricing is everywhere anyway")
    return {"response": response, "before": before, "after": held.holds(root), "removed": HELD}


@then("the removal is rejected because something still points at it")
def _rejected_while_pointed_at(client, attempt):
    assert attempt["response"].faults
    assert {fault.rule for fault in attempt["response"].faults} == {"on_delete"}
    assert attempt["after"] == attempt["before"]
    assert not read(client, attempt["removed"]).faults


@then("the client is given every link that blocks it")
def _every_blocking_link(attempt):
    assert [(fault.artifact, fault.place) for fault in attempt["response"].faults] == [(DECISION, "tags/0")]
    assert f"'{HELD}'" in attempt["response"].faults[0].message


@when("the client removes an artifact by a name the store holds nothing under, saying which role and why", target_fixture="attempt")
def _remove_nothing(root, client):
    before = held.holds(root)
    response = remove(client, "tag/seasonal", message="No more seasons")
    return {"response": response, "before": before, "after": held.holds(root)}


@then("the removal is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_for_nothing(attempt):
    assert [(fault.artifact, fault.rule) for fault in attempt["response"].faults] == [("tag/seasonal", "not-found")]
    assert "'tag/seasonal'" in attempt["response"].faults[0].message


@then("the store holds what it held before")
def _held_as_before(attempt):
    assert attempt["after"] == attempt["before"]


PROCESS = "process/run-the-clearance-sale"
TAGGED_PROCESS_TYPE = {
    "title": "Process",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {"title": {"type": "string"}},
        "required": ["title"],
        "parts": {"steps": {"items": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "about": {
                    "type": "string",
                    "ref": {"targets": ["tag"], "cardinality": "one", "parts": False, "on_delete": "refuse"},
                },
            },
            "required": ["title"],
        }}},
    },
}


@given("a process one of whose steps points at the tag nothing else points at")
def _a_step_pointing_at_the_loose_tag(client):
    define(client, TAGGED_PROCESS_TYPE)
    create(client, "process", {"title": "Run the clearance sale", "steps": [
        {"title": "Mark the shelves"}, {"title": "Price the stock", "about": LOOSE},
    ]})


@when("the client removes that tag, saying which role and why", target_fixture="attempt")
def _remove_the_tag_a_step_points_at(root, client):
    before = held.holds(root)
    response = remove(client, LOOSE, message="Nothing is on clearance")
    return {"response": response, "before": before, "after": held.holds(root), "removed": LOOSE}


@then("the client is given that link among the links that block it")
def _the_steps_link_among_them(client, attempt):
    faults = attempt["response"].faults
    assert [(fault.artifact, fault.place) for fault in faults] == [(PROCESS, "steps/1/about")]
    assert f"'{LOOSE}'" in faults[0].message
    assert not read(client, LOOSE).faults


@given("the client has removed the tag nothing points at")
def _the_loose_tag_removed(client):
    response = remove(client, LOOSE, message="Nothing is on clearance")
    assert not response.faults, response.faults


@when("the client creates a tag with the title the removed one had, saying which role and why", target_fixture="created")
def _create_a_tag_titled_as_the_removed_one(client):
    return request(client, "tag", "Clearance", {}, message="Clearance is back")


@then("the client is given the name the removed tag had, with no number added")
def _the_same_name(created):
    assert not created.faults, created.faults
    assert created.id == LOOSE


@then("the new tag is at its first version")
def _at_its_first_version(client, created):
    assert created.revision == 1
    assert read(client, LOOSE).revision == 1


TAGGED = "decision/clearance-runs-monthly"


@given(
    "one client is removing the tag while another is creating a decision that points at it, each saying which role "
    "and why",
    target_fixture="racing",
)
def _removing_while_linking(root):
    return {
        "removing the tag": ("Remove", removing(LOOSE, message="Nothing is on clearance")),
        "creating the decision": ("Create", creating("decision", "Clearance runs monthly", message="Say how often", content={
            "tags": [LOOSE],
            "sections": [
                {"title": "Purpose", "body": "Clear old stock.\n"},
                {"title": "Rationale", "body": "Stock ages monthly.\n"},
            ],
        })),
    }


@when(
    parsers.re("the client (?P<first>removing the tag|creating the decision) lands its change first"),
    target_fixture="attempt",
)
def _one_lands_first(root, racing, first):
    [second] = set(racing) - {first}
    attempt = {"removed": LOOSE}

    def landing_first():
        rpc, request_sent = racing[first]
        response = answer(getattr(kb_client.connect(root), rpc)(request_sent))
        assert not response.faults, response.faults
        attempt["before"] = held.holds(root)

    attempt["response"] = at_once.landed_second(at_once.OnAThread(root, *racing[second]), landing_first)
    attempt["after"] = held.holds(root)
    return attempt


@then("the new decision is rejected because a link must land on a node of a kind the type allows")
def _new_decision_rejected_for_its_link(attempt):
    assert [(fault.artifact, fault.place, fault.rule) for fault in attempt["response"].faults] == [
        (TAGGED, "tags/0", "ref"),
    ]
    assert attempt["response"].faults[0].message.startswith("a link must land on a node of a kind the type allows")
    assert f"'{LOOSE}'" in attempt["response"].faults[0].message
    assert attempt["after"] == attempt["before"]


@then("the store holds the tag and the decision that points at it")
def _tag_and_decision_held(client):
    assert not read(client, LOOSE).faults
    assert read(client, TAGGED).faults == []
    assert [fault.rule for fault in remove(client, LOOSE).faults] == ["on_delete"]


@then("the store holds neither the tag nor the new decision")
def _neither_held(client):
    assert [fault.rule for fault in read(client, LOOSE).faults] == ["not-found"]
    assert [fault.rule for fault in read(client, TAGGED).faults] == ["not-found"]
