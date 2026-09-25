import subprocess

from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, TAG_TYPE, create, define, everything_under, journal, listing, read, remove, tagged_decision_type
from kb import client as kb_client
from kb.contract import kb_pb2

scenarios("remove-an-artifact.feature")

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
    assert not (root / "kb" / f"{LOOSE}.yaml").exists()
    assert list(listing(client, "tag", ids_only=True).ids) == [HELD]


@then("the removal is recorded like any other change")
def _recorded(client, root, removed):
    entry = journal(client, LOOSE).entries[-1]
    assert (entry.op, entry.revision, entry.actor.role, entry.message, entry.batch) == (
        "delete", 2, "client", "Nothing is on clearance", entry.id,
    )
    assert removed.revision == 2
    git = ["git", "-C", str(root / "kb")]
    assert subprocess.run([*git, "log", "-1", "--format=%an%x09%s"], capture_output=True, text=True, check=True).stdout.strip() == (
        "client\tNothing is on clearance"
    )
    changed = subprocess.run([*git, "show", "--name-status", "--format=", "HEAD"], capture_output=True, text=True, check=True).stdout
    assert f"D\t{LOOSE}.yaml" in changed.splitlines()


@when("the client removes the tag the decision points at, saying which role and why", target_fixture="attempt")
def _remove_the_held_tag(root, client):
    before = everything_under(root)
    response = remove(client, HELD, message="Pricing is everywhere anyway")
    return {"response": response, "before": before, "after": everything_under(root)}


@then("the removal is rejected because something still points at it")
def _rejected_while_pointed_at(client, attempt):
    assert attempt["response"].faults
    assert {fault.rule for fault in attempt["response"].faults} == {"on_delete"}
    assert attempt["after"] == attempt["before"]
    assert not read(client, HELD).faults


@then("the client is given every link that blocks it")
def _every_blocking_link(attempt):
    assert [(fault.artifact, fault.path) for fault in attempt["response"].faults] == [(DECISION, "tags/0")]
    assert f"'{HELD}'" in attempt["response"].faults[0].message


@when("the client removes an artifact by a name the store holds nothing under, saying which role and why", target_fixture="attempt")
def _remove_nothing(root, client):
    before = everything_under(root)
    response = remove(client, "tag/seasonal", message="No more seasons")
    return {"response": response, "before": before, "after": everything_under(root)}


@then("the removal is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_for_nothing(attempt):
    assert [(fault.artifact, fault.rule) for fault in attempt["response"].faults] == [("tag/seasonal", "not-found")]
    assert "'tag/seasonal'" in attempt["response"].faults[0].message


@then("the store holds what it held before")
def _held_as_before(attempt):
    assert attempt["after"] == attempt["before"]
