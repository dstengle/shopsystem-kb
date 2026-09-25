from pytest_bdd import given, scenarios, then, when

from calls import CLIENT, DECISION_TYPE, WORK_ITEM_TYPE, create, define, next_version
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


WEEKLY = "decision/price-reviews-happen-weekly"


def _store_with_a_decision(root):
    """A client over a new store holding the decision type and one decision that fits it."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    define(client, DECISION_TYPE)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    return client


@given("a store where everything fits its type", target_fixture="client")
def _store_where_everything_fits(root):
    client = _store_with_a_decision(root)
    define(client, WORK_ITEM_TYPE)
    create(client, "work-item", {"title": "Move the review to Mondays", "decisions": [WEEKLY]})
    return client


@given(
    "a store where one artifact is missing a section its type requires and another points at something the store "
    "does not hold",
    target_fixture="client",
)
def _store_with_two_faults(root):
    """Both faults are made by hand behind the store's back, since the store refuses to write either."""
    client = _store_with_a_decision(root)
    define(client, WORK_ITEM_TYPE)
    create(client, "work-item", {"title": "Move the review to Mondays", "decisions": [WEEKLY]})
    decision = root / "kb" / "decision" / "price-reviews-happen-weekly.yaml"
    held = canonical.load(decision.read_text())
    held["sections"] = held["sections"][:1]
    decision.write_text(canonical.dump(held))
    work_item = root / "kb" / "work-item" / "move-the-review-to-mondays.yaml"
    held = canonical.load(work_item.read_text())
    held["decisions"] = ["decision/prices-are-reviewed-monthly"]
    work_item.write_text(canonical.dump(held))
    return client


@then("both are reported, each naming the artifact, the place in it and the rule broken")
def _both_reported(checked):
    assert not checked.faults, checked.faults
    assert [(fault.artifact, fault.path, fault.rule) for fault in checked.violations] == [
        (WEEKLY, "sections", "sections"),
        ("work-item/move-the-review-to-mondays", "decisions/0", "ref"),
    ]


@then("the client is told of no violation")
def _no_violation(checked):
    assert not checked.faults, checked.faults
    assert list(checked.violations) == []
    assert list(checked.stale) == []


@given(
    "a store where a decision was last checked against an older version of the decision type",
    target_fixture="client",
)
def _store_with_a_decision_behind_its_type(root):
    client = _store_with_a_decision(root)
    next_version(client, "decision", DECISION_TYPE)
    return client


@given(
    "a store where a decision was last checked against an older version of the decision type, and no longer fits "
    "the current version",
    target_fixture="client",
)
def _store_with_a_decision_behind_its_type_that_no_longer_fits(root):
    client = _store_with_a_decision(root)
    next_version(client, "decision", DECISION_TYPE, sections=["Purpose", "Rationale", "Review"])
    return client


@then("that decision is listed as behind its type")
def _listed_as_stale(checked):
    assert [(entry.artifact, entry.schema_version, entry.current) for entry in checked.stale] == [(WEEKLY, 1, 2)]


@then("it is not reported as a violation")
def _not_a_violation(checked):
    assert list(checked.violations) == []


@then("it is also reported as a violation, naming the artifact, the place in it and the rule broken")
def _also_a_violation(checked):
    assert [(fault.artifact, fault.path, fault.rule, fault.message) for fault in checked.violations] == [
        (WEEKLY, "sections", "sections",
         "the sections the type requires must all be present, in order; 'Review' is missing"),
    ]


@then("the check itself does not fail")
def _the_check_does_not_fail(checked):
    assert isinstance(checked, kb_pb2.ValidateResponse)
    assert not checked.faults, checked.faults
