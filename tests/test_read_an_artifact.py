import re

import pytest
from pytest_bdd import given, parsers, scenario, scenarios, then, when

from calls import CLIENT, PROCESS_TYPE, TAG_TYPE, WORK_ITEM_TYPE, create, define, read, tagged_decision_type, replace
import held
from kb import client as kb_client
from kb.content import loads
from kb.contract import kb_pb2

scenarios("find-the-store.feature")
scenarios("read-an-artifact.feature")


@scenario("name-what-is-asked-for.feature", "A name that is not a plain name is refused")
def test_a_name_that_is_not_a_plain_name_is_refused():
    pass


@scenario("name-what-is-asked-for.feature", "A name that begins at the root of the disk is refused")
def test_a_name_that_begins_at_the_root_of_the_disk_is_refused():
    pass


@scenario("name-what-is-asked-for.feature", "A place inside an artifact that is not a plain place is refused")
def test_a_place_inside_an_artifact_that_is_not_a_plain_place_is_refused():
    pass


@scenario("name-what-is-asked-for.feature", "Reading something the store does not hold is refused")
def test_reading_something_the_store_does_not_hold_is_refused():
    pass


@scenario("name-what-is-asked-for.feature", "A read that names a place the artifact does not hold is refused")
def test_a_read_that_names_a_place_the_artifact_does_not_hold_is_refused():
    pass


OLDER = "decision/prices-are-reviewed-monthly"
DECISION = "decision/price-reviews-happen-weekly"
PROCESS = "process/open-the-shop"
OLDER_SECTIONS = [
    {"title": "Purpose", "body": "Keep prices current.\n"},
    {"title": "Rationale", "body": "Monthly was enough once.\n"},
]


@given(
    "a store holding a decision that supersedes an older decision, has a purpose and a rationale, "
    "carries two options, and is pointed at by two work items",
    target_fixture="client",
)
def _store_with_a_linked_decision(root):
    return _start_with_a_linked_decision(root)


def _start_with_a_linked_decision(root):
    """Start a store at root holding the decision, what it supersedes, and two work items pointing at it."""
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
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
    assert {(stub.field, stub.id, stub.kind, stub.title) for stub in summary.references} == {
        ("supersedes", OLDER, "decision", "Prices are reviewed monthly"),
    }
    assert [(stub.collection, stub.id, stub.title) for stub in summary.parts] == [
        ("options", "keep-weekly", "Keep weekly"),
        ("options", "go-monthly", "Go monthly"),
    ]


@then("how many things point at it, counted by their kind and by the link they use")
def _inbound_counts(summary):
    assert [(count.kind, count.field, count.count) for count in summary.inbound] == [
        ("work-item", "decisions", 2),
    ]


@given("the client is working in a folder deep inside the directory the store sits in")
def _working_deep_inside_the_store(root, monkeypatch):
    monkeypatch.chdir(_deep_inside(root))
    monkeypatch.delenv("KB_ROOT", raising=False)


def _deep_inside(directory):
    """A folder a few levels down inside `directory`, made."""
    deep = directory / "shelves" / "pricing" / "notes"
    deep.mkdir(parents=True)
    return deep


def _elsewhere(tmp_path):
    """A directory inside no store, made."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    return elsewhere


def _another_store(tmp_path):
    """A second store, started beside the one the scenario reads from."""
    other = tmp_path / "other"
    other.mkdir()
    kb_client.connect(other).Init(kb_pb2.InitRequest(root=str(other), actor=CLIENT))
    return other


@pytest.fixture
def readied():
    """The client a scenario readied before it read, if one did; otherwise the read readies its own."""
    return None


@when("the client reads the decision", target_fixture="shown")
def _read_the_decision_from_here(readied):
    if readied is None:
        return read(kb_client.connect(), DECISION)
    readied["used"] = readied["client"]
    return read(readied["client"], DECISION)


@then("the client is given the decision, from the store found above where it is working")
def _from_the_store_above(shown):
    assert (shown.id, shown.title) == (DECISION, "Price reviews happen weekly")


@when("the client reads an artifact by a name the store holds nothing under", target_fixture="shown")
def _read_a_name_the_store_lacks(client):
    return read(client, "decision/nothing-of-the-sort")


@then("the read is rejected because the store holds nothing by that name, and the name asked for is given back")
def _rejected_as_not_held(shown):
    assert [(fault.artifact, fault.rule) for fault in shown.faults] == [("decision/nothing-of-the-sort", "not-found")]
    assert "decision/nothing-of-the-sort" in shown.faults[0].message


@when(parsers.parse('the client reads an artifact by the name "{name}"'), target_fixture="shown")
def _read_by_the_name(client, name):
    return read(client, name)


@then("the read is rejected because a name is a kind and a plain name of lower-case letters, digits and single hyphens")
def _rejected_as_not_a_plain_name(shown):
    assert [fault.rule for fault in shown.faults] == ["locator"]
    assert "plain name" in shown.faults[0].message


@then("no content comes back, from inside the store or outside it")
def _no_content_at_all(shown):
    assert (shown.id, shown.title, shown.content) == ("", "", "")
    assert not shown.references and not shown.parts and not shown.inbound


@when("the client reads an artifact by a name that begins at the root of the disk", target_fixture="shown")
def _read_by_an_absolute_name(client, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.yaml").write_text("title: Not for the store\n")
    return read(client, str(outside / "secret"))


@then("the read is rejected because a name is a kind and a plain name, never a path")
def _rejected_as_a_path(shown):
    assert [fault.rule for fault in shown.faults] == ["locator"]
    assert "never a path" in shown.faults[0].message


PLACES = {
    'the place "sections/../.." inside the decision': "sections/../..",
    'the place "sections/nowhere" inside the decision': "sections/nowhere",
    'the place "sections/purpose/body/first" inside the decision, which runs on past a piece of prose':
        "sections/purpose/body/first",
}
SECTIONS_NOT_HELD = {
    'the section of the decision titled "Consequences", which it holds no section under': "Consequences",
}


@pytest.fixture
def asked():
    """What a read asked for, filled in by the When that made it."""
    return {}


@when(parsers.re(f"the client reads (?P<what>{'|'.join(map(re.escape, PLACES))})"), target_fixture="shown")
def _read_a_place_inside(client, asked, what):
    asked["what"] = PLACES[what]
    return client.Read(kb_pb2.ReadRequest(locator=kb_pb2.Locator(id=DECISION, place=PLACES[what])))


@when(parsers.re(f"the client reads (?P<what>{'|'.join(map(re.escape, SECTIONS_NOT_HELD))})"), target_fixture="shown")
def _read_a_section_not_held(client, asked, what):
    asked["what"] = SECTIONS_NOT_HELD[what]
    return read(client, DECISION, section=SECTIONS_NOT_HELD[what])


@then("the read is rejected because the decision holds nothing at that place, and what was asked for is given back")
def _rejected_for_nothing_at_that_place(shown, asked):
    assert [(fault.artifact, fault.rule) for fault in shown.faults] == [(DECISION, "not-found")]
    assert repr(asked["what"]) in shown.faults[0].message


@then(
    "the read is rejected because a place inside an artifact is named by parts of the same plain alphabet, "
    "or a collection and an item in it"
)
def _rejected_as_not_a_plain_place(shown):
    assert [(fault.artifact, fault.place, fault.rule) for fault in shown.faults] == [(DECISION, "sections/../..", "locator")]
    assert "plain alphabet" in shown.faults[0].message


@given("the client is working outside any store, with KB_ROOT naming this one")
def _outside_with_kb_root_naming_this_one(root, tmp_path, monkeypatch):
    monkeypatch.chdir(_elsewhere(tmp_path))
    monkeypatch.setenv("KB_ROOT", str(root))


@then("the client is given the decision, from the store KB_ROOT names")
def _from_the_store_kb_root_names(shown):
    assert (shown.id, shown.title) == (DECISION, "Price reviews happen weekly")


@given("the client is working outside any store and nothing names one", target_fixture="elsewhere")
def _outside_with_nothing_naming_one(tmp_path, monkeypatch):
    elsewhere = _elsewhere(tmp_path)
    monkeypatch.chdir(elsewhere)
    monkeypatch.delenv("KB_ROOT", raising=False)
    return elsewhere


@then("the read is rejected because no store was found, neither above where it is working nor named outright")
def _rejected_with_no_store_found(shown, elsewhere):
    assert [fault.rule for fault in shown.faults] == ["store"]
    assert "no store was found" in shown.faults[0].message
    assert str(elsewhere) in shown.faults[0].message


@given("the client is working outside any store, with KB_ROOT naming a directory that holds no store", target_fixture="empty")
def _outside_with_kb_root_naming_nothing(tmp_path, monkeypatch):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(_elsewhere(tmp_path))
    monkeypatch.setenv("KB_ROOT", str(empty))
    return empty


@then("the read is rejected because KB_ROOT names a directory that holds no store")
def _rejected_as_kb_root_holds_no_store(shown, empty):
    assert [fault.rule for fault in shown.faults] == ["store"]
    assert "KB_ROOT names a directory that holds no store" in shown.faults[0].message
    assert str(empty) in shown.faults[0].message


@then("no content comes back")
def _no_content(shown):
    assert (shown.id, shown.title, shown.content) == ("", "", "")


@given("the client is working inside a store, with KB_ROOT naming a different store", target_fixture="other")
def _inside_one_store_with_kb_root_naming_another(root, tmp_path, monkeypatch):
    other = _another_store(tmp_path)
    monkeypatch.chdir(_deep_inside(root))
    monkeypatch.setenv("KB_ROOT", str(other))
    return other


@then(
    "the read is rejected because KB_ROOT names a store other than the one it is working in, "
    "and neither of the two is guessed at"
)
def _rejected_as_two_stores(shown, root, other):
    assert [fault.rule for fault in shown.faults] == ["store"]
    assert "KB_ROOT names a store other than the one" in shown.faults[0].message
    assert str(root) in shown.faults[0].message and str(other) in shown.faults[0].message


@then("no content comes back, from either store")
def _no_content_from_either(shown):
    assert (shown.id, shown.title, shown.content) == ("", "", "")
    assert not shown.references and not shown.parts and not shown.inbound


REMOVED_FROM = {
    "a directory outside any store": lambda root, tmp_path: _elsewhere(tmp_path),
    "a folder deep inside the directory the store sits in": lambda root, tmp_path: _deep_inside(root),
    "a folder deep inside the directory a different store sits in":
        lambda root, tmp_path: _deep_inside(_another_store(tmp_path)),
}


def _work_in_then_remove(directory, monkeypatch):
    """Move the process into `directory`, then take the directory away from under it."""
    monkeypatch.chdir(directory)
    directory.rmdir()


@given(parsers.parse("the client is working in {where}, which has since been removed, and nothing names a store"))
def _removed_with_nothing_naming_one(where, root, tmp_path, monkeypatch):
    _work_in_then_remove(REMOVED_FROM[where](root, tmp_path), monkeypatch)
    monkeypatch.delenv("KB_ROOT", raising=False)


@given(parsers.parse("the client is working in {where}, which has since been removed, with KB_ROOT naming this store"))
def _removed_with_kb_root_naming_this_one(where, root, tmp_path, monkeypatch):
    _work_in_then_remove(REMOVED_FROM[where](root, tmp_path), monkeypatch)
    monkeypatch.setenv("KB_ROOT", str(root))


@given("the client is working in a directory that has since been removed, and nothing names a store")
def _removed_outside_with_nothing_naming_one(root, tmp_path, monkeypatch):
    _removed_with_nothing_naming_one("a directory outside any store", root, tmp_path, monkeypatch)


@then("the client is given that refusal as it is given any other fault, the call never breaking off")
def _given_the_refusal_as_an_answer(shown):
    assert isinstance(shown, kb_pb2.ReadResponse)
    assert [fault.rule for fault in shown.faults] == ["store"]


@then("the read is rejected because the directory it is working in is gone")
def _rejected_as_working_directory_gone(shown):
    assert [fault.rule for fault in shown.faults] == ["store"]
    assert "the working directory is gone" in shown.faults[0].message


@given(
    "the client was readied to call a store while working where there was none and nothing named one",
    target_fixture="readied",
)
def _readied_where_there_is_no_store(tmp_path, monkeypatch):
    here = tmp_path / "shop"
    here.mkdir()
    monkeypatch.chdir(here)
    monkeypatch.delenv("KB_ROOT", raising=False)
    return {"client": kb_client.connect(), "store_there": held.holds_anything_in_the_place(here), "here": here}


@given("a store holding the decision has since been started where the client is working")
def _store_started_since(readied):
    _start_with_a_linked_decision(readied["here"])


@then("the client is given the decision")
def _given_the_decision(shown):
    assert not shown.faults, shown.faults
    assert (shown.id, shown.title) == (DECISION, "Price reviews happen weekly")


@then("the client was never readied again after the store appeared")
def _never_readied_again(readied):
    assert readied["store_there"] is False
    assert readied["used"] is readied["client"]


DAILY = "decision/stock-is-counted-daily"
NIGHTLY = "decision/stock-is-counted-nightly"
COUNTING = [
    {"title": "Purpose", "body": "Know what is on the shelves.\n"},
    {"title": "Rationale", "body": "Counting catches shrinkage early.\n"},
]


@given("two decisions that point at each other")
def _two_decisions_pointing_at_each_other(client):
    create(client, "decision", {"title": "Stock is counted daily", "sections": COUNTING})
    create(client, "decision", {"title": "Stock is counted nightly", "supersedes": DAILY, "sections": COUNTING})
    changed = replace(client, DAILY, {"supersedes": NIGHTLY, "sections": COUNTING}, message="Point back")
    assert not changed.faults, changed.faults


@when("the client reads the whole of one of them following its links three steps", target_fixture="whole")
def _read_one_following_three_steps(client):
    response = read(client, DAILY, whole=True, depth=3)
    assert not response.faults, response.faults
    return response


@then("the other decision is given in place of the link")
def _the_other_filled_in(whole):
    other = loads(whole.content)["supersedes"]
    assert (other["id"], other["title"]) == (NIGHTLY, "Stock is counted nightly")
    assert other["sections"] == COUNTING


@then("where that one points back, the decision being read is given as a name rather than filled in again")
def _points_back_as_a_name(whole):
    assert whole.id == DAILY
    assert loads(whole.content)["supersedes"]["supersedes"] == DAILY


@when("the client reads the rationale of the decision", target_fixture="shown")
def _read_the_rationale(client):
    return read(client, DECISION, section="Rationale")


@then("the client is given that section and nothing else")
def _that_section_alone(shown):
    assert not shown.faults, shown.faults
    assert loads(shown.content) == {"title": "Rationale", "body": "Costs move weekly.\n"}
    assert not shown.references and not shown.parts and not shown.inbound


@when("the client reads the whole decision", target_fixture="whole")
@when("the client reads the whole decision without asking for its links to be followed", target_fixture="whole")
def _read_the_whole_decision(client):
    response = read(client, DECISION, whole=True)
    assert not response.faults, response.faults
    return response


@then("the client is given every field, every section and every part, in the order the type declares")
def _everything_in_declared_order(whole):
    assert (whole.id, whole.type, whole.schema_version, whole.revision, whole.title) == (
        DECISION, "decision", 1, 1, "Price reviews happen weekly",
    )
    content = loads(whole.content)
    assert list(content) == ["supersedes", "sections", "options"]
    assert [section["title"] for section in content["sections"]] == ["Purpose", "Rationale"]
    assert [list(option) for option in content["options"]] == [["id", "title", "body"]] * 2
    assert [option["id"] for option in content["options"]] == ["keep-weekly", "go-monthly"]


@then("the older decision is given as the name it is known by, and nothing more")
def _older_as_a_name(whole):
    assert loads(whole.content)["supersedes"] == OLDER


@when(
    parsers.re(r"the client reads the whole (?P<kind>decision|process) following its links (?P<steps>one step|two steps)"),
    target_fixture="whole",
)
def _read_the_whole_following(client, kind, steps):
    response = read(client, DECISION if kind == "decision" else PROCESS, whole=True, depth={"one step": 1, "two steps": 2}[steps])
    assert not response.faults, response.faults
    return response


@then("the older decision is given in place of the link, as the store holds it now")
def _older_as_stored(root, whole):
    assert loads(whole.content)["supersedes"] == held.artifact(root, OLDER)


@then("what the older decision itself points at is given as names")
def _older_links_as_names(whole):
    older = loads(whole.content)["supersedes"]
    assert not any(isinstance(value, dict) for value in older.values())
    assert all(isinstance(target, str) for target in older.get("tags", []))


@given(parsers.parse('the older decision is tagged "{tag}"'))
def _older_decision_tagged(client, tag):
    define(client, TAG_TYPE)
    tagged = create(client, "tag", {"title": tag})
    changed = replace(client, OLDER, {"tags": [tagged.id], "sections": OLDER_SECTIONS}, message="Tag it")
    assert not changed.faults, changed.faults


@then("the older decision is given in place of the link")
def _older_filled_in(whole):
    older = loads(whole.content)["supersedes"]
    assert (older["id"], older["title"], older["sections"]) == (OLDER, "Prices are reviewed monthly", OLDER_SECTIONS)


@then("the tag is given in place of the link inside the older decision")
def _tag_filled_in(whole):
    assert loads(whole.content)["supersedes"]["tags"] == [
        {"id": "tag/pricing", "type": "tag", "schema_version": 1, "revision": 1, "title": "pricing"},
    ]


@given("a store holding a process whose steps branch to other steps of the same process")
def _process_whose_steps_branch(client):
    define(client, PROCESS_TYPE)
    create(client, "process", {"title": "Open the shop", "steps": [
        {"title": "Check the till", "body": "Is the float there?", "branches": ["count-the-float", "call-the-manager"]},
        {"title": "Count the float", "body": "Count it into the till."},
        {"title": "Call the manager", "body": "The float is missing."},
    ]})


@then("the branches are given as written, naming the steps of that process")
def _branches_as_written(whole):
    steps = loads(whole.content)["steps"]
    assert steps[0]["branches"] == ["count-the-float", "call-the-manager"]
    assert set(steps[0]["branches"]) <= {step["id"] for step in steps}


@then("the older decision comes with its name, its kind, its title and the version it is at, ahead of its content")
def _older_says_what_it_is(whole):
    older = loads(whole.content)["supersedes"]
    assert list(older)[:5] == ["id", "type", "schema_version", "revision", "title"]
    assert (older["id"], older["type"], older["title"], older["revision"]) == (
        OLDER, "decision", "Prices are reviewed monthly", 1,
    )


KB_ROOTS = {
    "set to nothing at all": lambda tmp_path: "",
    "naming a directory that is not there": lambda tmp_path: str(tmp_path / "not-there"),
    "naming a file rather than a directory": lambda tmp_path: str(_a_file(tmp_path)),
}


def _a_file(tmp_path):
    path = tmp_path / "a-file"
    path.write_text("not a store\n")
    return path


@given(
    parsers.re(f"the client is working outside any store, with KB_ROOT (?P<state>{'|'.join(map(re.escape, KB_ROOTS))})"),
    target_fixture="kb_root",
)
def _outside_with_kb_root(tmp_path, monkeypatch, state):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    named = KB_ROOTS[state](tmp_path)
    monkeypatch.setenv("KB_ROOT", named)
    return named


@then("the read is rejected because KB_ROOT names no store, and KB_ROOT is named back")
def _rejected_as_kb_root_names_no_store(shown, kb_root):
    assert [(fault.rule, fault.message) for fault in shown.faults] == [
        ("store", f"KB_ROOT names a directory that holds no store: {kb_root}"),
    ]


@then("where the client is working is not fallen back on")
def _not_fallen_back_on(shown, tmp_path):
    message = shown.faults[0].message
    assert "no store was found" not in message
    assert str(tmp_path / "elsewhere") not in message and not message.endswith(".")
