from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, create, define
from kb import canonical, client as kb_client
from kb.contract import kb_pb2

scenarios("check-the-store.feature")

MANGLED = "title: [a bracket opened by hand and never closed\n"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


@given(
    "a store where someone edited a decision's file by hand and left it in a shape the store cannot read",
    target_fixture="client",
)
def _store_with_a_file_mangled_by_hand(root):
    """Two decisions edited by hand: one left unreadable, one left readable but without the body of its purpose."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, "decision", {"title": "Prices are reviewed monthly", "sections": SECTIONS})
    (root / "kb" / "decision" / "price-reviews-happen-weekly.yaml").write_text(MANGLED)
    monthly = root / "kb" / "decision" / "prices-are-reviewed-monthly.yaml"
    held = canonical.load(monthly.read_text())
    del held["sections"][0]["body"]
    monthly.write_text(canonical.dump(held))
    return client


@when("the client checks the store", target_fixture="checked")
def _check_the_store(client):
    return client.Validate(kb_pb2.ValidateRequest())


@then("that file is reported as a violation, naming the file")
def _reported_as_unreadable(checked):
    unreadable = [fault for fault in checked.violations if fault.rule == "unreadable"]
    assert [fault.artifact for fault in unreadable] == ["decision/price-reviews-happen-weekly"]
    assert "decision/price-reviews-happen-weekly.yaml cannot be read" in unreadable[0].message


@then("everything else in the store is checked and reported alongside it")
def _the_rest_checked_alongside(checked):
    assert [(fault.artifact, fault.path, fault.rule) for fault in checked.violations] == [
        ("decision/price-reviews-happen-weekly", "", "unreadable"),
        ("decision/prices-are-reviewed-monthly", "sections/0", "required"),
    ]


@then("the check comes back with its answer rather than breaking off")
def _answers(checked):
    assert isinstance(checked, kb_pb2.ValidateResponse)
    assert not checked.faults, checked.faults
