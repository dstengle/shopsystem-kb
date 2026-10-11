"""A set of creates or of replacements asked to be checked only (decision/check-only-sets) is a read: it answers as
landing the same set then answers, the set's name aside; it writes nothing, reads no clock and is never refused as
busy; and it is answered while a server owns the store, asked of the store directly or through the server, where it is
not taken under the server's lock."""
import threading

import pytest

from calls import (
    DECISION_TYPE, NOTE_TYPE, TAG_TYPE, TYPES, WORK_ITEM_TYPE, create, create_many, created, define, iri,
    placeholders, read, replace, replace_many, replaced, start_a_store,
)
import held
import serving
from kb import client as kb_client, testing as kb_testing

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
DECISION = iri("decision", "price-reviews-happen-weekly")
OPTION = f"{DECISION}#options/go-weekly"
NOTE = iri("note", "on-going-weekly")
WORK_ITEM = iri("work-item", "move-the-review-to-mondays")
SECOND_WORK_ITEM = iri("work-item", "print-the-new-price-labels")
MONTHLY = iri("decision", "prices-are-reviewed-monthly")
DAILY = iri("decision", "price-reviews-happen-daily")
NEW_WORK_ITEM = iri("work-item", "review-prices-on-mondays")
PATIENCE = 30.0  # seconds a test waits for an answer before it fails


def _store(root):
    """A store holding a decision with an option a note points into, and two work items, the first of them replaced
    once, so standing at its second revision."""
    client = kb_client.connect(root)
    start_a_store(root)
    for each in (DECISION_TYPE, WORK_ITEM_TYPE, NOTE_TYPE):
        define(client, each)
    create(client, "decision", {
        "title": "Price reviews happen weekly", "sections": SECTIONS, "options": [{"title": "Go weekly"}],
    })
    create(client, "note", {"title": "On going weekly", "about": OPTION})
    create(client, "work-item", {"title": "Move the review to Mondays"})
    create(client, "work-item", {"title": "Print the new price labels"})
    assert replace(client, WORK_ITEM, {"decisions": []}).revision == 2
    return client


def _creates(*items, message="Make several changes"):
    return lambda client, only: create_many(client, list(items), message=message, check_only=only)


def _replacements(*items):
    return lambda client, only: replace_many(client, list(items), check_only=only)


# Each set, asked of the store `_store` gives, and the rule of every fault it is refused with, none when it lands.
SETS = {
    "sound creates, one pointing at the other": (_creates(
        created("work-item", "Review prices on Mondays", {"decisions": [MONTHLY]}),
        created("decision", "Prices are reviewed monthly", {"sections": SECTIONS}),
    ), []),
    "sound replacements": (_replacements(
        replaced(WORK_ITEM, {"decisions": [DECISION]}), replaced(SECOND_WORK_ITEM, {"decisions": [DECISION]}),
    ), []),
    "one fault": (_creates(
        created("decision", "Prices are reviewed monthly", {"sections": SECTIONS}),
        created("decision", "Price reviews happen daily", {"sections": SECTIONS[:1]}),
    ), ["sections"]),
    "several faults across changes": (_creates(
        created("decision", "Prices are reviewed monthly", {"sections": []}),
        created("work-item", "Review prices on Mondays", {"decisions": 7}),
        created("decision", "Price reviews happen daily", {"sections": [], "supersedes": WORK_ITEM}),
    ), ["sections", "sections", "type", "ref", "sections", "sections"]),
    "a create at an IRI already held": (_creates(
        created("decision", "Prices are reviewed monthly", {"sections": SECTIONS}),
        created("decision", "Price reviews happen weekly", {"sections": SECTIONS}),
    ), ["identity"]),
    "a create naming a version not held": (_creates(
        created("decision", "Prices are reviewed monthly", {"sections": SECTIONS}, version=9),
    ), ["version"]),
    "a replacement saying a revision its artifact has moved from": (_replacements(
        replaced(WORK_ITEM, {}, revision=1), replaced(SECOND_WORK_ITEM, {}),
    ), ["revision"]),
    "two changes to one artifact": (_replacements(
        replaced(WORK_ITEM, {"decisions": [DECISION]}), replaced(WORK_ITEM, {}, revision=3),
    ), []),
    "a type defined and artifacts of it created": (_creates(
        created(TYPES, "Tag", {key: TAG_TYPE[key] for key in ("version", "schema")}),
        created("tag", "Urgent", {}),
        created("tag", "Later", {}),
    ), []),
    "an artifact created before the type it is of is defined": (_creates(
        created("tag", "Urgent", {}),
        created(TYPES, "Tag", {key: TAG_TYPE[key] for key in ("version", "schema")}),
    ), ["version"]),
    "a replacement dropping a part something points into": (_replacements(
        replaced(SECOND_WORK_ITEM, {}), replaced(DECISION, {"sections": SECTIONS}),
    ), ["on_delete"]),
    "a replacement of what is not held": (_replacements(
        replaced(SECOND_WORK_ITEM, {}), replaced(MONTHLY, {"sections": SECTIONS}),
    ), ["not-found"]),
    "a link to what its field does not allow": (_replacements(
        replaced(SECOND_WORK_ITEM, {"decisions": [WORK_ITEM]}),
    ), ["ref"]),
    "two creates carrying one IRI": (_creates(
        created("decision", "Prices are reviewed monthly", {"sections": SECTIONS}),
        created("decision", "Prices are reviewed monthly", {"sections": SECTIONS}),
    ), ["identity"]),
    "an empty set": (_creates(), ["operations"]),
    "a set that does not say why": (_creates(
        created("decision", "Prices are reviewed monthly", {"sections": SECTIONS}), message="",
    ), ["message"]),
}


@pytest.mark.parametrize("case", SETS)
def test_a_set_checked_only_is_answered_as_landing_the_same_set_then_answers_but_for_its_name(root, case):
    ask, rules = SETS[case]
    client = _store(root)
    before = held.holds(root)
    checked = ask(client, True)
    assert held.holds(root) == before
    landed = ask(client, False)
    assert [fault.rule for fault in landed.faults] == rules
    assert checked.faults == landed.faults
    assert checked.refused == landed.refused
    if not landed.refused:
        assert list(checked.results) == list(landed.results) and len(landed.results) > 0
        assert (checked.batch, bool(landed.batch)) == ("", True)


def _the_clock_is_never_read():
    raise AssertionError("a check reads no clock")


WRITING_NOTHING = {
    "creates, a type and a placeholder among them": _creates(
        created(TYPES, "Tag", {key: TAG_TYPE[key] for key in ("version", "schema")}),
        created("tag", "Urgent", {}),
        created("work-item", "Review prices on Mondays", {"decisions": [MONTHLY]}),
    ),
    "replacements, one moving a link": _replacements(
        replaced(WORK_ITEM, {"decisions": [DECISION]}), replaced(NOTE, {"about": DECISION}),
    ),
    "a set refused": _replacements(replaced(WORK_ITEM, {"decisions": 7})),
}


@pytest.mark.parametrize("case", WRITING_NOTHING)
def test_a_set_checked_only_writes_nothing_and_reads_no_clock(root, case):
    client = _store(root)
    kept = held.holds(root)
    files, history = held.bytes_held(root), held.history(client)
    seen = {
        "names": held.names(root), "versions": held.versions(root), "waiting": placeholders(client).response,
        "revisions": [read(client, name).revision for name in held.names(root)],
    }
    answered = WRITING_NOTHING[case](kb_client.connect(root, clock=_the_clock_is_never_read), True)
    assert answered.refused == (case == "a set refused"), answered.faults
    assert held.bytes_held(root) == files
    assert (held.holds(root), held.history(client)) == (kept, history)
    assert seen == {
        "names": held.names(root), "versions": held.versions(root), "waiting": placeholders(client).response,
        "revisions": [read(client, name).revision for name in held.names(root)],
    }


def _sound(client, only=True):
    """A set of creates and a set of replacements, each sound, and each change's result as landing it would give."""
    return [
        (create_many(client, [
            created("decision", "Prices are reviewed monthly", {"sections": SECTIONS}),
            created("work-item", "Review prices on Mondays", {"decisions": [MONTHLY]}),
        ], check_only=only), [(MONTHLY, 1), (NEW_WORK_ITEM, 1)]),
        (replace_many(client, [
            replaced(WORK_ITEM, {"decisions": [DECISION]}, revision=2), replaced(SECOND_WORK_ITEM, {}),
        ], check_only=only), [(WORK_ITEM, 3), (SECOND_WORK_ITEM, 2)]),
    ]


def _answered_as_they_would_land(sets):
    for answered, results in sets:
        assert not answered.refused, answered.faults
        assert [(result.id, result.revision) for result in answered.results] == results
        assert answered.batch == ""


def test_a_set_checked_only_is_answered_while_another_change_holds_the_write_lock(root, request, monkeypatch):
    client = _store(root)
    holding = held.another_change_holds(root, request, monkeypatch)
    _answered_as_they_would_land(_sound(client))
    holding.let_go()
    assert held.holds(root) == holding.held


def test_a_set_checked_only_asked_of_a_served_store_directly_is_answered_and_one_to_land_is_refused(root, tmp_path):
    client = _store(root)
    before = held.holds(root)["rows"]
    with kb_testing.served(root, tmp_path / "arranged"):
        _answered_as_they_would_land(_sound(client))
        assert [[fault.rule for fault in answered.faults] for answered, _ in _sound(client, only=False)] == [
            ["served"], ["served"],
        ]
    assert held.holds(root)["rows"] == before


def test_a_set_checked_only_asked_through_a_server_is_answered_as_it_is_in_process(root, tmp_path):
    client = _store(root)
    before, in_process = held.holds(root)["rows"], _sound(client)
    with kb_testing.served(root, tmp_path / "arranged"):
        through_the_server = _sound(kb_client.connect(tmp_path / "arranged"))
        _answered_as_they_would_land(through_the_server)
        assert through_the_server == in_process
    assert held.holds(root)["rows"] == before


def test_a_client_readied_with_a_clock_asks_a_server_for_a_set_to_be_checked_only_and_is_answered(root, tmp_path):
    _store(root)
    with kb_testing.served(root, tmp_path / "arranged"):
        _answered_as_they_would_land(_sound(kb_client.connect(tmp_path / "arranged", clock=_the_clock_is_never_read)))


def test_a_set_checked_only_asked_through_a_server_is_not_taken_under_the_lock_its_changes_are(root, tmp_path, request):
    _store(root)
    hosting = serving.hosted(root, request, None)
    serving.connection(tmp_path / "arranged", str(hosting.address))
    client, answered = kb_client.connect(tmp_path / "arranged"), []
    asking = threading.Thread(target=lambda: answered.extend(_sound(client)), daemon=True)
    with hosting.taking:
        asking.start()
        asking.join(PATIENCE)
        waited = asking.is_alive()
    asking.join(PATIENCE)
    assert not waited, "the check waited for the lock the server takes its changes under"
    _answered_as_they_would_land(answered)
