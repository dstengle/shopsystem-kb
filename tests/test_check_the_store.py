from pytest_bdd import given, parsers, scenario, then, when

from calls import (
    DECISION_TYPE, MISORDERED_DECISION, ORDERED_DECISION_TYPE, READING_ORDER, WORK_ITEM_TYPE, create, define, iri,
    next_version, placeholders, replace, start_a_store, targets,
)
import held
from kb import client as kb_client


@scenario("check-the-store.feature", "A store holding links to IRIs it does not hold lists each placeholder with what links to it")
def test_a_store_holding_links_to_iris_it_does_not_hold_lists_each_placeholder_with_what():
    pass


@scenario("check-the-store.feature", "A store whose only findings are placeholders reports no violation")
def test_a_store_whose_only_findings_are_placeholders_reports_no_violation():
    pass


@scenario("check-the-store.feature", "An artifact behind its type is checked against the version of its type it conforms to")
def test_an_artifact_behind_its_type_is_checked_against_the_version_of_its_type_it_confor():
    pass


@scenario("check-the-store.feature", "An artifact that conforms to a version of its type a later version has followed is listed as behind its type")
def test_an_artifact_that_conforms_to_a_version_of_its_type_a_later_version_has_followed():
    pass


@scenario("query-the-store.feature", "The client asks for the placeholders")
def test_the_client_asks_for_the_placeholders():
    pass


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


SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]


WEEKLY = iri("decision", "price-reviews-happen-weekly")


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
    work_item = held.artifact(root, iri("work-item", "move-the-review-to-mondays"))
    work_item["decisions"] = [iri("decision", "prices-are-reviewed-monthly")]
    held.plant(root, iri("work-item", "move-the-review-to-mondays"), work_item)
    return client


@then("both are reported, each naming the artifact, the place in it and the rule broken")
def _both_reported(checked):
    assert not checked.faults, checked.faults
    assert [(fault.artifact, fault.place, fault.rule) for fault in checked.violations] == [
        (WEEKLY, "sections", "sections"),
        (iri("work-item", "move-the-review-to-mondays"), "decisions/0", "ref"),
    ]


@then("the client is told of no violation")
def _no_violation(checked):
    assert not checked.faults, checked.faults
    assert list(checked.violations) == []
    assert list(checked.stale) == []


@given("a store holding a decision that conforms to the first version of the decision type", target_fixture="client")
def _store_with_a_decision_of_the_first_version(root):
    return _store_with_a_decision(root)


@given("a second version of the decision type has followed it")
def _a_second_version_has_followed(client):
    """The second version requires a section the decision does not have."""
    followed = next_version(client, "decision", DECISION_TYPE, ["Purpose", "Rationale", "Consequences"])
    assert not followed.faults, followed.faults


@given(parsers.re(r"the decision (?P<how>fits the first version but not the second|does not fit the first version)"))
def _the_decision_fits(root, how):
    """Made by hand behind the store's back, since the store refuses to write a decision that does not fit."""
    if how.startswith("does not"):
        decision = held.artifact(root, WEEKLY)
        decision["sections"] = decision["sections"][:1]
        held.plant(root, WEEKLY, decision)


@then("that decision is listed as behind its type")
def _listed_as_stale(checked):
    assert [(entry.artifact, entry.schema_version, entry.current) for entry in checked.stale] == [(WEEKLY, 1, 2)]


@then("it is not reported as a violation")
def _not_a_violation(checked):
    assert list(checked.violations) == []


@then("it is reported as a violation, naming the artifact, the place in it and the rule broken")
def _a_violation(checked):
    assert [(fault.artifact, fault.place, fault.rule) for fault in checked.violations] == [
        (WEEKLY, "sections", "sections"),
    ]


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
    identity = {key: stored[key] for key in ("id", "type", "revision", "title")}
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


def _to_a_decision():
    return {"type": "string", "ref": {"targets": targets("decision"), "cardinality": "one", "parts": False,
                                      "on_delete": "refuse"}}


# A decision that may supersede one decision and revisit another; a work item that serves a decision and whose steps
# each may need one.
LINKING_DECISION_TYPE = {"title": "Decision", "version": 1, "schema": {
    "type": "object",
    "properties": {"title": {"type": "string"}, "supersedes": _to_a_decision(), "revisits": _to_a_decision()},
    "required": ["title"],
}}
STEPPED_WORK_ITEM_TYPE = {"title": "Work item", "version": 1, "schema": {
    "type": "object",
    "properties": {"title": {"type": "string"}, "decision": _to_a_decision()},
    "required": ["title"],
    "parts": {"steps": {"items": {
        "type": "object", "properties": {"title": {"type": "string"}, "needs": _to_a_decision()}, "required": ["title"],
    }}},
}}
NOT_HELD = {
    "first": iri("decision", "prices-are-reviewed-monthly"), "second": iri("decision", "prices-are-reviewed-yearly"),
}
HOLDING = {"decision": iri("decision", "prices-are-reviewed-daily"), "work item": iri("work-item", "move-the-review")}
OLDER = iri("decision", "prices-are-reviewed-hourly")
# What a step calls a link's place, as the field holding it and the place kb gives for it.
SITS_AT = {
    "what it supersedes": ("supersedes", "supersedes"), "the decision it serves": ("decision", "decision"),
    "its first step": ("needs", "steps/0/needs"), "its second step": ("needs", "steps/1/needs"),
}


def _links(datatable):
    """A step's table of links as (the IRI not held, the artifact holding the link, the field, the place)."""
    heading, *rows = datatable
    assert heading == ["IRI not held", "artifact holding the link", "place the link sits at"]
    return [
        (NOT_HELD[target], HOLDING[holder.split(" ", 1)[1]], *SITS_AT[where]) for target, holder, where in rows
    ]


def _written(links, holder):
    """The content of the artifact a step's links sit in, each link written at its place."""
    content = {}
    for target, _, _, place in (link for link in links if link[1] == holder):
        *above, field = place.split("/")
        node = content
        if above:
            items = content.setdefault(above[0], [])
            items.extend({"title": f"Step {number + 1}"} for number in range(len(items), int(above[1]) + 1))
            node = items[int(above[1])]
        node[field] = target
    return content


@given("a store where these links point at IRIs the store does not hold:", target_fixture="client")
def _store_with_links_to_iris_not_held(root, datatable):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, LINKING_DECISION_TYPE)
    define(client, STEPPED_WORK_ITEM_TYPE)
    links = _links(datatable)
    create(client, "decision", {"title": "Daily", **_written(links, HOLDING["decision"])}, at=HOLDING["decision"])
    create(client, "work-item", {"title": "Move", **_written(links, HOLDING["work item"])}, at=HOLDING["work item"])
    return client


@given("the decision also points at an older decision the store holds")
def _the_decision_also_points_at_a_held_decision(client):
    create(client, "decision", {"title": "Hourly"}, at=OLDER)
    answered = replace(client, HOLDING["decision"], {"supersedes": NOT_HELD["first"], "revisits": OLDER})
    assert not answered.faults, answered.faults


@when("the client asks for the placeholders", target_fixture="asked")
def _ask_for_the_placeholders(client):
    return placeholders(client)


@then("the client is given the first IRI and the second IRI and nothing else")
def _given_the_two_iris(asked):
    assert not asked.faults, asked.faults
    assert sorted(each.id for each in asked.placeholders) == sorted([NOT_HELD["first"], NOT_HELD["second"]])


@then("each comes with these links into it and no others:")
def _each_with_its_links(asked, datatable):
    given = [
        (each.id, link.artifact, link.field, link.place, link.part)
        for each in asked.placeholders for link in each.links
    ]
    assert sorted(given) == sorted((*link, "") for link in _links(datatable))
