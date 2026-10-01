from pytest_bdd import given, scenario, then

from calls import (
    DECISION_TYPE, MISORDERED_DECISION, ORDERED_DECISION_TYPE, READING_ORDER, WORK_ITEM_TYPE, create, define,
    next_version, start_a_store,
)
import held
from kb import client as kb_client
from kb.contract import kb_pb2


@scenario("check-the-store.feature", "A store with nothing wrong reports nothing")
def test_a_store_with_nothing_wrong_reports_nothing():
    pass


@scenario("check-the-store.feature", "Every violation is reported")
def test_every_violation_is_reported():
    pass


@scenario(
    "check-the-store.feature", "An artifact's violations are given in the order its places stand when it reads back"
)
def test_an_artifacts_violations_are_given_in_reading_order():
    pass


@scenario("check-the-store.feature", "An artifact behind its type is reported as stale")
def test_an_artifact_behind_its_type_is_reported_as_stale():
    pass


@scenario("check-the-store.feature", "An artifact behind its type that no longer fits it is reported both ways")
def test_an_artifact_behind_its_type_that_no_longer_fits_it_is_reported_both_ways():
    pass


SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


WEEKLY = "decision/price-reviews-happen-weekly"


def _store_with_a_decision(root):
    """A client over a new store holding the decision type and one decision that fits it."""
    client = kb_client.connect(root)
    start_a_store(root)
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
    decision = held.artifact(root, WEEKLY)
    decision["sections"] = decision["sections"][:1]
    held.plant(root, WEEKLY, decision)
    work_item = held.artifact(root, "work-item/move-the-review-to-mondays")
    work_item["decisions"] = ["decision/prices-are-reviewed-monthly"]
    held.plant(root, "work-item/move-the-review-to-mondays", work_item)
    return client


@then("both are reported, each naming the artifact, the place in it and the rule broken")
def _both_reported(checked):
    assert not checked.faults, checked.faults
    assert [(fault.artifact, fault.place, fault.rule) for fault in checked.violations] == [
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
    assert [(fault.artifact, fault.place, fault.rule, fault.message) for fault in checked.violations] == [
        (WEEKLY, "sections", "sections",
         "the sections the type requires must all be present, in order; 'Review' is missing"),
    ]


@then("the check itself does not fail")
def _the_check_does_not_fail(checked):
    assert isinstance(checked.response, kb_pb2.CheckResponse)
    assert not checked.faults, checked.faults


@given(
    "a store holding a decision type that declares its fields first, then its required sections, then its "
    "collection of options",
    target_fixture="client",
)
def _store_with_a_decision_type_in_reading_order(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, ORDERED_DECISION_TYPE)
    return client


@given(
    "the store holds a decision stored with its options first, then its sections, then its fields, where a field "
    "breaks two rules of the type, the second option is of a shape the type does not allow, and the rationale is "
    "missing"
)
def _the_store_holds_a_misordered_decision(root, client):
    """Made by hand behind the store's back, since the store refuses to write it."""
    created = create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    stored = held.artifact(root, created.id)
    identity = {key: stored[key] for key in ("id", "type", "schema_version", "revision", "title")}
    held.plant(root, created.id, {**identity, **MISORDERED_DECISION})


@then("the decision's violations are reported, each naming the artifact, the place in it and the rule broken")
def _the_decisions_violations_are_reported(checked):
    assert not checked.faults, checked.faults
    assert {fault.artifact for fault in checked.violations} == {WEEKLY}
    assert sorted((fault.place, fault.rule) for fault in checked.violations) == sorted(READING_ORDER)


@then(
    "they come in the order the places stand in the decision as it reads back: the field first, then the sections, "
    "then the options"
)
def _violations_in_reading_order(checked):
    assert [fault.place for fault in checked.violations] == [place for place, _ in READING_ORDER]


@then("the two violations at the field come in the alphabetical order of the names of the rules they break")
def _two_violations_at_the_field_in_rule_order(checked):
    assert [fault.rule for fault in checked.violations if fault.place == "status"] == ["maxLength", "pattern"]
