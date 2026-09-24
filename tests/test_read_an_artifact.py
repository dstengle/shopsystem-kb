from pytest_bdd import given, parsers, scenarios, then, when

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


@when("the client reads an artifact by a name the store holds nothing under", target_fixture="refused")
def _read_a_name_the_store_lacks(client):
    return read(client, "decision/nothing-of-the-sort")


@then("the read is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_as_not_held(refused):
    assert [(fault.artifact, fault.rule) for fault in refused.faults] == [("decision/nothing-of-the-sort", "not-found")]
    assert "decision/nothing-of-the-sort" in refused.faults[0].message


@when(parsers.parse('the client reads an artifact by the name "{name}"'), target_fixture="refused")
def _read_by_the_name(client, name):
    return read(client, name)


@then("the read is rejected because a name is a kind and a plain name of lower-case letters, digits and single hyphens")
def _rejected_as_not_a_plain_name(refused):
    assert [fault.rule for fault in refused.faults] == ["locator"]
    assert "plain name" in refused.faults[0].message


@then("no content comes back, from inside the store or outside it")
def _no_content_at_all(refused):
    assert (refused.id, refused.title, refused.content) == ("", "", "")
    assert not refused.references and not refused.parts and not refused.inbound


@when("the client reads an artifact by a name that begins at the root of the disk", target_fixture="refused")
def _read_by_an_absolute_name(client, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.yaml").write_text("title: Not for the store\n")
    return read(client, str(outside / "secret"))


@then("the read is rejected because a name is a kind and a plain name, never a path")
def _rejected_as_a_path(refused):
    assert [fault.rule for fault in refused.faults] == ["locator"]
    assert "never a path" in refused.faults[0].message


@when(parsers.parse('the client reads the place "{place}" inside the decision'), target_fixture="refused")
def _read_a_place_inside(client, place):
    return client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=DECISION, path=place)))


@then(
    "the read is rejected because a place inside an artifact is named by parts of the same plain alphabet, "
    "or a collection and an item in it"
)
def _rejected_as_not_a_plain_place(refused):
    assert [(fault.artifact, fault.path, fault.rule) for fault in refused.faults] == [(DECISION, "sections/../..", "locator")]
    assert "plain alphabet" in refused.faults[0].message


@given("the client is working outside any store, with KB_ROOT naming this one")
def _outside_with_kb_root_naming_this_one(root, tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("KB_ROOT", str(root))


@then("the client is given the decision, from the store KB_ROOT names")
def _from_the_store_kb_root_names(shown):
    assert (shown.id, shown.title) == (DECISION, "Price reviews happen weekly")


@given("the client is working outside any store and nothing names one", target_fixture="elsewhere")
def _outside_with_nothing_naming_one(tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.delenv("KB_ROOT", raising=False)
    return elsewhere


@then("the read is rejected because no store was found, neither above where it is working nor named outright")
def _rejected_with_no_store_found(shown, elsewhere):
    assert [fault.rule for fault in shown.faults] == ["store"]
    assert "no store was found" in shown.faults[0].message
    assert str(elsewhere) in shown.faults[0].message
