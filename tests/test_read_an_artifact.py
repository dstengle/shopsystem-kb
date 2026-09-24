from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define, read
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

scenarios("read-an-artifact.feature")

OLDER = "decision/prices-are-reviewed-monthly"
DECISION = "decision/price-reviews-happen-weekly"


@given(
    "a store holding a decision that supersedes an older decision, has a purpose and a rationale, "
    "carries two options, and is pointed at by two work items",
    target_fixture="client",
)
def _store_with_a_linked_decision(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    define(client, WORK_ITEM_TYPE)
    create(client, "decision", {
        "title": "Prices are reviewed monthly",
        "sections": [
            {"title": "Purpose", "body": "Keep prices current.\n"},
            {"title": "Rationale", "body": "Monthly was enough once.\n"},
        ],
    })
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "supersedes": OLDER,
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
        "options": [
            {"title": "Keep weekly", "body": "Review every Monday."},
            {"title": "Go monthly", "body": "Review on the first of the month."},
        ],
    })
    create(client, "work-item", {"title": "Move the review to Mondays", "decisions": [DECISION]})
    create(client, "work-item", {"title": "Tell the pricing team", "decisions": [DECISION]})
    return client


@when("the client reads the decision at a glance", target_fixture="summary")
def _read_at_a_glance(client):
    return read(client, DECISION)


@then("the client is given its name, its kind, its title and the few fields the type shows at a glance")
def _identity_and_summary_fields(summary):
    assert (summary.id, summary.type, summary.title) == (DECISION, "decision", "Price reviews happen weekly")
    assert loads(summary.content) == {"supersedes": OLDER}


@then("a stub of each thing it points at and of each of its parts")
def _stubs(summary):
    assert {(stub.field, stub.id, stub.type, stub.title) for stub in summary.references} == {
        ("supersedes", OLDER, "decision", "Prices are reviewed monthly"),
    }
    assert [(stub.collection, stub.id, stub.title) for stub in summary.parts] == [
        ("options", "keep-weekly", "Keep weekly"),
        ("options", "go-monthly", "Go monthly"),
    ]


@then("how many things point at it, counted by their kind and by the link they use")
def _inbound_counts(summary):
    assert [(count.type, count.field, count.count) for count in summary.inbound] == [
        ("work-item", "decisions", 2),
    ]


@given("the client is working in a folder deep inside the directory the store sits in")
def _working_deep_inside_the_store(root, monkeypatch):
    deep = root / "shelves" / "pricing" / "notes"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    monkeypatch.delenv("KB_ROOT", raising=False)


@when("the client reads the decision", target_fixture="shown")
def _read_the_decision_from_here():
    return read(kb_client.connect(), DECISION)


@then("the client is given the decision, from the store found above where it is working")
def _from_the_store_above(shown):
    assert (shown.id, shown.title) == (DECISION, "Price reviews happen weekly")
