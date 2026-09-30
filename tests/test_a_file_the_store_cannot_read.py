import re

from pytest_bdd import given, parsers, scenario, then, when

from calls import (
    CLIENT, DECISION_TYPE, MANGLED, PROCESS_TYPE, TAG_TYPE, append, create, define, everything_under, journal,
    listing, refs, remove, request, search, write,
)
from kb import client as kb_client
from kb.contract import kb_pb2


@scenario("answer-a-damaged-file.feature", "Every call refuses a file it cannot read, naming the file")
def test_every_call_refuses_a_file_it_cannot_read_naming_the_file():
    pass


@scenario("answer-a-damaged-file.feature", "Creating an artifact of a kind whose type cannot be read is refused")
def test_creating_an_artifact_of_a_kind_whose_type_cannot_be_read_is_refused():
    pass


@scenario("answer-a-damaged-file.feature", "An entry of the history that cannot be read is refused in the same way")
def test_an_entry_of_the_history_that_cannot_be_read_is_refused_in_the_same_way():
    pass


@scenario("check-the-store.feature", "Every shape of damage to a stored file is the one named finding")
def test_every_shape_of_damage_to_a_stored_file_is_the_one_named_finding():
    pass


DECISION = "decision/price-reviews-happen-weekly"
SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]

CALLS = {
    "replaces the decision, saying which role and why":
        lambda client: write(client, DECISION, {"sections": SECTIONS}),
    "adds an item to a collection of the decision, saying which role and why":
        lambda client: append(client, DECISION, "options", {"title": "Go monthly"}),
    "removes the decision, saying which role and why":
        lambda client: remove(client, DECISION),
    "lists the decisions":
        lambda client: listing(client, "decision"),
    "searches the prose for a word that decision holds":
        lambda client: search(client, "weekly"),
    "follows the links into the decision":
        lambda client: refs(client, DECISION, 1, inward=True),
    "follows the links out of the decision":
        lambda client: refs(client, DECISION, 1),
    "creates a decision with a title and both required sections, saying which role and why":
        lambda client: request(client, "decision", "Close early on Sundays", {"sections": SECTIONS}),
    "reads the journal":
        lambda client: journal(client),
}


@given("a store holding a decision, a process and a tag, each of a kind the store holds a type for",
       target_fixture="client")
def _store_with_a_decision_a_process_and_a_tag(root):
    client = kb_client.connect(root)
    client.Init(kb_pb2.InitRequest(root=str(root), actor=CLIENT))
    for type_content in (DECISION_TYPE, PROCESS_TYPE, TAG_TYPE):
        define(client, type_content)
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS})
    create(client, "process", {"title": "Open the shop", "steps": [{"title": "Unlock"}, {"title": "Count the float"}]})
    create(client, "tag", {"title": "Pricing"})
    return client


@when(parsers.re(f"the client (?P<call>{'|'.join(map(re.escape, CALLS))})"), target_fixture="answered")
def _the_client_calls(client, root, before, call):
    before.update(held=everything_under(root))
    return CALLS[call](client)


@then("the call is rejected because that file cannot be read, and the file is named")
def _rejected_as_unreadable(answered):
    assert [(fault.artifact, fault.rule) for fault in answered.faults] == [(DECISION, "unreadable")]
    assert f"{DECISION}.yaml cannot be read" in answered.faults[0].message


@then("the client is given that fault as it is given any other, the call never breaking off")
def _given_as_any_other_fault(answered):
    assert type(answered).__module__ == kb_pb2.__name__
    assert answered.faults


@then("nothing is written anywhere in the store")
def _nothing_written(root, before):
    assert everything_under(root) == before["held"]


DAMAGE = {
    "in a shape that cannot be read at all": lambda held: "title: [a bracket opened by hand and never closed\n",
    "empty, with nothing in it": lambda held: "",
    "holding a list rather than a set of named entries": lambda held: "- title: Price reviews happen weekly\n- revision: 1\n",
    "holding a second document after the first": lambda held: held + "---\n" + held,
    "telling a reader how to build one of its values": lambda held: held + "reviewed: !!str Monday\n",
    "pointing back at a value written elsewhere in it": lambda held: held + "reviewed: &day Monday\ndecided: *day\n",
    "naming the same entry twice": lambda held: held + "title: Price reviews happen monthly\n",
}


@given(parsers.re(f"someone edited the decision's file by hand and left it (?P<damage>{'|'.join(map(re.escape, DAMAGE))})"))
def _decision_file_damaged_by_hand(root, damage):
    """The Background's decision left damaged in one way, the rest of what it wrote left as it was."""
    decision = root / "kb" / f"{DECISION}.yaml"
    decision.write_text(DAMAGE[damage](decision.read_text()))


@then("everything else in the store is checked and reported alongside it")
def _the_rest_checked_alongside(checked):
    assert [(fault.artifact, fault.path, fault.rule) for fault in checked.violations] == [(DECISION, "", "unreadable")]
    assert list(checked.stale) == []


@given("someone edited the decision type's file by hand and left it in a shape the store cannot read")
def _decision_type_mangled_by_hand(root):
    (root / "kb" / "schema" / "decision.yaml").write_text(MANGLED)


@given(
    "someone edited one of the store's history entries by hand and left it in a shape the store cannot read",
    target_fixture="entry",
)
def _history_entry_mangled_by_hand(root):
    """The newest entry of the Background's history left unreadable; where it is, from the store's own directory."""
    entry = sorted((root / "kb" / "journal").rglob("*.yaml"))[-1]
    entry.write_text(MANGLED)
    return entry.relative_to(root / "kb")


@then("the create is rejected because that file cannot be read, and the file is named")
def _create_rejected_as_unreadable(answered):
    assert [(fault.artifact, fault.rule) for fault in answered.faults] == [("schema/decision", "unreadable")]
    assert "schema/decision.yaml cannot be read" in answered.faults[0].message
    assert (answered.id, answered.revision) == ("", 0)


@then("the read is rejected because that file cannot be read, and the file is named")
def _read_rejected_as_unreadable(answered, entry):
    assert [(fault.artifact, fault.rule) for fault in answered.faults] == [("", "unreadable")]
    assert f"{entry} cannot be read" in answered.faults[0].message
    assert list(answered.entries) == []
