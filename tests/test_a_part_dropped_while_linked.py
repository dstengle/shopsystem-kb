"""A change that drops a part something outside its set links into is refused, each link in the way named, in the
order of the names of the artifacts holding them, a link from an artifact the same set changes or removes judged as
the set leaves it; and a set checked only (decision/check-only-sets) is answered exactly as landing it is. Each answer
expected here is the one a landing gave while only the adapter found these links, inside its landing transaction.
Through kb.write's own `land` and `checked`, so that a set of more than one kind of change, which the contract does
not take, can be asked; each store under its own tmp_path."""
import pytest

from calls import DECISION_TYPE, NOTE_TYPE, create, define, iri, placeholders, read, start_a_store
import held
from kb import changes, client as kb_client, signatures, store, values, write
from kb.content import dumps
from kb.signatures import Signed

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
AGAIN = [SECTIONS[0], {"title": "Rationale", "body": "Costs now move daily.\n"}]
WEEKLY_OPTION, DAILY_OPTION = {"title": "Go weekly"}, {"title": "Go daily"}
DECISION = iri("decision", "price-reviews-happen-weekly")
WEEKLY, DAILY, MONTHLY = (f"{DECISION}#options/go-{each}" for each in ("weekly", "daily", "monthly"))
WHY = iri("note", "why-weekly")
ON_WEEKLY = iri("note", "on-going-weekly")
ON_DAILY = iri("note", "on-going-daily")
WAITS = iri("note", "on-going-monthly")
ANNUAL = iri("decision", "annual-reviews")
YEARLY = f"{ANNUAL}#options/go-yearly"
ABOUT_YEARLY = iri("note", "about-going-yearly")
WAITING = [(DECISION, [(WAITS, "about", "about", "options/go-monthly")])]


def _store(root):
    """A store holding a decision with two options: two notes point into the first, the one whose name comes later
    made first, one note into the second, and one into an option the decision was created without, so waiting; and a
    second decision, its name before the first's, with an option a note points into."""
    client = kb_client.connect(root)
    start_a_store(root)
    for each in (DECISION_TYPE, NOTE_TYPE):
        define(client, each)
    create(client, "note", {"title": "On going monthly", "about": MONTHLY})
    create(client, "decision", {
        "title": "Price reviews happen weekly", "sections": SECTIONS, "options": [WEEKLY_OPTION, DAILY_OPTION],
    })
    create(client, "note", {"title": "Why weekly", "about": WEEKLY})
    create(client, "note", {"title": "On going weekly", "about": WEEKLY})
    create(client, "note", {"title": "On going daily", "about": DAILY})
    create(client, "decision", {"title": "Annual reviews", "sections": SECTIONS, "options": [{"title": "Go yearly"}]})
    create(client, "note", {"title": "About going yearly", "about": YEARLY})
    assert _waiting(client) == WAITING
    return client


def _waiting(client):
    return [
        (each.id, [(link.artifact, link.field, link.place, link.part) for link in each.links])
        for each in placeholders(client).placeholders
    ]


def _replace(name, content):
    return changes.Replace(values.Locator(values.artifact_id(name), ()), values.content(dumps(content)))


def _remove(name):
    return changes.Remove(values.Locator(values.artifact_id(name), ()))


def _keeping(*options, sections=SECTIONS):
    return _replace(DECISION, {"sections": sections, "options": list(options)})


def _in_the_way(option, note):
    return (note, "about", "on_delete", f"{option!r} cannot be removed while {note!r} points at it at 'about'")


# Each set, asked of the store `_store` gives, and every fault it is refused with, none when it lands.
SETS = {
    "a part another artifact links into": ([_keeping(WEEKLY_OPTION)], [_in_the_way(DAILY, ON_DAILY)]),
    "a part two artifacts link into": (
        [_keeping(DAILY_OPTION)], [_in_the_way(WEEKLY, ON_WEEKLY), _in_the_way(WEEKLY, WHY)],
    ),
    "two parts, each linked into": (
        [_keeping()],
        [_in_the_way(DAILY, ON_DAILY), _in_the_way(WEEKLY, ON_WEEKLY), _in_the_way(WEEKLY, WHY)],
    ),
    "a part linked into, after a change to the artifact that keeps it": (
        [_keeping(WEEKLY_OPTION, DAILY_OPTION, sections=AGAIN), _keeping(WEEKLY_OPTION)],
        [_in_the_way(DAILY, ON_DAILY)],
    ),
    "parts of two artifacts, each linked into, the artifact whose name comes later changed first": (
        [_keeping(WEEKLY_OPTION), _replace(ANNUAL, {"sections": SECTIONS})],
        [_in_the_way(DAILY, ON_DAILY), _in_the_way(YEARLY, ABOUT_YEARLY)],
    ),
    "a part linked into by an artifact the set removes": ([_keeping(WEEKLY_OPTION), _remove(ON_DAILY)], []),
    "a part linked into by an artifact the set removes first": ([_remove(ON_DAILY), _keeping(WEEKLY_OPTION)], []),
    "a part linked into by an artifact the set replaces so that it links elsewhere": (
        [_keeping(WEEKLY_OPTION), _replace(ON_DAILY, {"about": WEEKLY})], [],
    ),
    "a part linked into by an artifact the set replaces so that it links nowhere": (
        [_replace(ON_DAILY, {}), _keeping(WEEKLY_OPTION)], [],
    ),
    "a part linked into by one artifact the set moves away and by one it leaves": (
        [_keeping(DAILY_OPTION), _replace(ON_WEEKLY, {"about": DAILY})], [_in_the_way(WEEKLY, WHY)],
    ),
    "a part linked into by an artifact the set replaces and leaves linking there": (
        [_keeping(WEEKLY_OPTION), _replace(ON_DAILY, {"about": DAILY})],
        [(ON_DAILY, "about", "ref", f"a link must land on a node of a kind the type allows; {DAILY!r} does not")],
    ),
    "a part linked into, beside a change that does not fit its type": (
        [_keeping(WEEKLY_OPTION), _replace(WHY, {"about": 7})], [(WHY, "about", "type", "7 is not of type 'string'")],
    ),
    "no part, a link waiting on one the artifact never had": (
        [_keeping(WEEKLY_OPTION, DAILY_OPTION, sections=AGAIN)], [],
    ),
}


def _answered(root, ask) -> list:
    """Every fault a set asked of the store was refused with, whole; none when it was answered."""
    with store.opened(root) as opened:
        try:
            ask(opened)
        except values.Refused as refused:
            return [(fault.artifact, fault.place, fault.rule, fault.message) for fault in refused.faults]
    return []


@pytest.mark.parametrize("case", SETS)
def test_a_set_dropping_a_part_is_answered_as_it_was_and_checked_only_as_it_lands(root, case):
    operations, expected = SETS[case]
    client = _store(root)
    before = held.holds(root)
    checked = _answered(root, lambda opened: write.checked(opened, operations))
    assert held.holds(root) == before
    landed = _answered(root, lambda opened: write.land(
        opened, operations, Signed(signatures.Actor("client", ""), "Change a decision"),
    ))
    assert landed == expected
    assert checked == landed
    assert (held.holds(root) == before) == bool(expected)
    assert _waiting(client) == WAITING
    assert read(client, DECISION).revision == (1 if expected else 1 + sum(
        each.locator.id == values.artifact_id(DECISION) for each in operations
    ))
