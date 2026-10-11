import copy

from pytest_bdd import given, parsers, scenario, then, when

from calls import (
    DECISION_TYPE, PROCESS_TYPE, TAG_TYPE, WORK_ITEM_TYPE, below_their_types, create, define, iri, read, refs, remove, replace, start_a_store,
    tagged_decision_type, targets, type_iri, version_iri,
)
from kb import client as kb_client


@scenario("query-the-store.feature", "The client follows links narrowed to a path below the type")
def test_the_client_follows_links_narrowed_to_a_path_below_the_type():
    pass


@scenario("query-the-store.feature", "The client follows the links out of an artifact")
def test_the_client_follows_the_links_out_of_an_artifact():
    pass


@scenario("query-the-store.feature", "The client follows the links into an artifact")
def test_the_client_follows_the_links_into_an_artifact():
    pass


@scenario("query-the-store.feature", "The client narrows the links to one link and one kind")
def test_the_client_narrows_the_links_to_one_link_and_one_kind():
    pass


@scenario("query-the-store.feature", "The client follows the links two steps out")
def test_the_client_follows_the_links_two_steps_out():
    pass


@scenario("query-the-store.feature", "The client follows the links out of one place inside an artifact")
def test_the_client_follows_the_links_out_of_one_place_inside_an_artifact():
    pass


@scenario("query-the-store.feature", "A link into a part counts as a link into the artifact holding it")
def test_a_link_into_a_part_counts_as_a_link_into_the_artifact_holding_it():
    pass


OLDER = iri("decision", "prices-are-reviewed-monthly")
DECISION = iri("decision", "price-reviews-happen-weekly")
OLDER_SECTIONS = [
    {"title": "Purpose", "body": "Keep prices current.\n"},
    {"title": "Rationale", "body": "Monthly was enough once.\n"},
]


@given("a store where a decision supersedes an older decision", target_fixture="client")
def _store_with_a_superseded_decision(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, TAG_TYPE)
    define(client, tagged_decision_type())
    define(client, WORK_ITEM_TYPE)
    create(client, "decision", {"title": "Prices are reviewed monthly", "sections": OLDER_SECTIONS})
    create(client, "decision", {
        "title": "Price reviews happen weekly",
        "supersedes": OLDER,
        "sections": [
            {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
            {"title": "Rationale", "body": "Costs move weekly.\n"},
        ],
    })
    return client


@given("two work items point at that decision")
def _two_work_items(client):
    create(client, "work-item", {"title": "Move the review to Mondays", "decisions": [DECISION]})
    create(client, "work-item", {"title": "Tell the pricing team", "decisions": [DECISION]})


@given(parsers.parse('the older decision is tagged "{tag}"'))
def _older_decision_tagged(client, tag):
    tagged = create(client, "tag", {"title": tag})
    changed = replace(client, OLDER, {"tags": [tagged.id], "sections": OLDER_SECTIONS}, message="Tag it")
    assert not changed.faults, changed.faults


@when("the client follows the links out of the decision two steps", target_fixture="reached")
def _follow_two_steps_out(client):
    response = refs(client, DECISION, depth=2)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given the older decision and the tag")
def _older_decision_and_tag(reached):
    assert [(found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        (OLDER, version_iri("decision"), "Prices are reviewed monthly"),
        (iri("tag", "pricing"), version_iri("tag"), "pricing"),
    ]


@then("each of them comes with the route taken to it")
def _each_with_its_route(reached):
    assert {found.stub.id: [(hop.field, hop.id) for hop in found.route] for found in reached} == {
        OLDER: [("supersedes", OLDER)],
        iri("tag", "pricing"): [("supersedes", OLDER), ("tags", iri("tag", "pricing"))],
    }


WORK_ITEMS = [iri("work-item", "move-the-review-to-mondays"), iri("work-item", "tell-the-pricing-team")]


@when("the client follows the links out of the decision", target_fixture="reached")
def _follow_out(client):
    response = refs(client, DECISION, depth=1)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of the older decision")
def _stub_of_the_older_decision(reached):
    assert [(found.stub.field, found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        ("supersedes", OLDER, version_iri("decision"), "Prices are reviewed monthly"),
    ]


@when("the client follows the links into the decision", target_fixture="reached")
def _follow_in(client):
    response = refs(client, DECISION, depth=1, inward=True)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of each work item")
def _stub_of_each_work_item(reached):
    assert [(found.stub.field, found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        ("decisions", WORK_ITEMS[0], version_iri("work-item"), "Move the review to Mondays"),
        ("decisions", WORK_ITEMS[1], version_iri("work-item"), "Tell the pricing team"),
    ]
    assert [[(hop.field, hop.id) for hop in found.route] for found in reached] == [
        [("decisions", WORK_ITEMS[0])], [("decisions", WORK_ITEMS[1])],
    ]


@when(
    "the client follows the links into the decision, only through the link a work item uses, and only from work items",
    target_fixture="reached",
)
def _follow_in_narrowed(client):
    response = refs(client, DECISION, depth=1, inward=True, via="decisions", type_name="work-item")
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given both work items and nothing else")
def _both_work_items(reached):
    assert [found.stub.id for found in reached] == WORK_ITEMS


ROADMAP = iri("decision", "roadmap")
PLAIN_WORK_ITEM_TYPE = {"title": "Work item", "version": 1, "schema": TAG_TYPE["schema"]}


def leading_decision_type():
    """The decision type, whose artifacts may also lead to decisions and work items."""
    decision_type = copy.deepcopy(DECISION_TYPE)
    decision_type["schema"]["properties"]["leads"] = {
        "type": "array",
        "items": {"type": "string"},
        "ref": {"targets": targets("decision", "work-item"), "cardinality": "many", "parts": False, "on_delete": "refuse"},
    }
    return decision_type


@given(parsers.parse('a store where a decision at "{path}" below its type points at each of these:'), target_fixture="client")
def _a_decision_pointing_below_types(root, path, datatable):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, PLAIN_WORK_ITEM_TYPE)
    define(client, leading_decision_type())
    pointed_at = below_their_types(datatable)
    for kind, at in pointed_at:
        create(client, kind, {"title": at, **({"sections": OLDER_SECTIONS} if kind == "decision" else {})}, at=at)
    create(client, "decision", {
        "title": "Roadmap", "leads": [at for _, at in pointed_at], "sections": OLDER_SECTIONS,
    }, at=iri("decision", path))
    return client


@when(
    parsers.parse('the client follows the links out of the decision at "{at}", narrowed to the path "{path}" below the type'),
    target_fixture="reached",
)
def _follow_out_narrowed_to_a_path(client, at, path):
    response = refs(client, iri("decision", at), depth=1, path=path)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given only these:")
def _only_these(reached, datatable):
    assert [(found.stub.id, found.stub.type) for found in reached] == [
        (at, version_iri(kind)) for kind, at in below_their_types(datatable)
    ]


PROCESS = iri("process", "open-the-shop")
INTO_A_STEP = iri("work-item", "check-the-till-float")


@given(
    "a store holding a process, and a work item that points at one step of that process rather than at the whole "
    "process"
)
def _a_work_item_pointing_into_a_process(client):
    define(client, PROCESS_TYPE)
    create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock the door"}, {"title": "Count the till"}]})
    following = copy.deepcopy(WORK_ITEM_TYPE["schema"])
    following["properties"]["follows"] = {
        "type": "string", "ref": {"targets": targets("process"), "cardinality": "one", "parts": True, "on_delete": "refuse"},
    }
    revised = replace(client, type_iri("work-item"), {"version": 2, "schema": following}, message="Let work items follow a step")
    assert not revised.faults, revised.faults
    create(client, "work-item", {"title": "Check the till float", "follows": f"{PROCESS}#steps/count-the-till"})


@when("the client follows the links into the process", target_fixture="reached")
def _follow_into_the_process(client):
    response = refs(client, PROCESS, depth=1, inward=True)
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of that work item")
def _a_stub_of_the_work_item(reached):
    assert [(found.stub.field, found.stub.id) for found in reached] == [("follows", INTO_A_STEP)]


@then("reading the process at a glance counts that work item among the things pointing at it")
def _counted_at_a_glance(client):
    summary = read(client, PROCESS)
    assert not summary.faults, summary.faults
    assert [(count.kind, count.field, count.count) for count in summary.inbound] == [(type_iri("work-item"), "follows", 1)]


@then("removing the process is refused while that work item points into it")
def _removal_refused(client):
    refused = remove(client, PROCESS)
    assert [(fault.artifact, fault.place, fault.rule) for fault in refused.faults] == [(INTO_A_STEP, "follows", "on_delete")]
    assert read(client, PROCESS).revision == 1


NOTE = iri("note", "weekly-reviews-need-cover")
NOTE_TYPE = {
    "title": "Note",
    "version": 1,
    "schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "decisions": copy.deepcopy(WORK_ITEM_TYPE["schema"]["properties"]["decisions"]),
        },
        "required": ["title"],
    },
}


@given("a note that is not a work item also points at the decision, through the same link the work items use")
def _a_note_pointing_at_the_decision(client):
    define(client, NOTE_TYPE)
    create(client, "note", {"title": "Weekly reviews need cover", "decisions": [DECISION]})


@given("one of the two work items points at the decision a second time, through a different link of its own")
def _a_work_item_pointing_twice(client):
    revised = copy.deepcopy(WORK_ITEM_TYPE["schema"])
    revised["properties"]["follows"] = {
        "type": "string", "ref": {"targets": targets("decision"), "cardinality": "one", "parts": False, "on_delete": "refuse"},
    }
    changed = replace(client, type_iri("work-item"), {"version": 2, "schema": revised}, message="Let work items follow a decision")
    assert not changed.faults, changed.faults
    changed = replace(client, WORK_ITEMS[1], {"decisions": [DECISION], "follows": DECISION}, message="Follow it too")
    assert not changed.faults, changed.faults
    inward = refs(client, DECISION, depth=1, inward=True)
    assert {(found.stub.field, found.stub.id) for found in inward.reached} >= {("decisions", NOTE)}


OPENING = iri("tag", "opening")


@given("a process one of whose steps points at a tag of its own, while another of its steps points at the decision")
def _a_process_whose_steps_point_out(client):
    process_type = copy.deepcopy(PROCESS_TYPE)
    process_type["schema"]["parts"]["steps"]["items"]["properties"]["uses"]["ref"]["targets"] = targets("tag", "decision")
    define(client, process_type)
    create(client, "tag", {"title": "opening"})
    create(client, "process", {"title": "Open the shop", "steps": [
        {"title": "Unlock the door", "uses": OPENING},
        {"title": "Check the prices", "uses": DECISION},
    ]})


@when("the client follows the links out of that step of the process", target_fixture="reached")
def _follow_out_of_a_step(client):
    response = refs(client, PROCESS, depth=1, place="steps/unlock-the-door")
    assert not response.faults, response.faults
    return list(response.reached)


@then("the client is given a stub of that tag and nothing else the process points at")
def _only_the_tag(reached):
    assert [(found.stub.field, found.stub.id, found.stub.type, found.stub.title) for found in reached] == [
        ("uses", OPENING, version_iri("tag"), "opening"),
    ]
    assert [[(hop.field, hop.id) for hop in found.route] for found in reached] == [[("uses", OPENING)]]
