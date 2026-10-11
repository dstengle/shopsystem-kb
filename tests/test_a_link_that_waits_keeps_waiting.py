"""Plain tests through the contract of decision/a-link-that-waits-keeps-waiting: a decision whose link into an option
of another decision was written while that other was not held, the other created since without the option, can still
be changed in every way that leaves the link as it is, and the link still waits; a link a change adds, or alters in
target or part, into a part a held artifact lacks is refused as any new one is; and the store's check and
`kb validate` say of it what they said before."""
import copy

import pytest

import at_once
import held
from calls import (
    DECISION_TYPE, add, add_many, added, check, define, iri, placeholders, read, remove, replace, replace_many,
    replaced, replacing, request, start_a_store, targets,
)
from conftest import _kb
from kb import client as kb_client

LINKING_TYPE = copy.deepcopy(DECISION_TYPE)
LINKING_TYPE["schema"]["properties"]["supersedes"]["ref"]["parts"] = True
LINKING_TYPE["schema"]["properties"]["builds_on"] = {
    "type": "array",
    "items": {"type": "string"},
    "ref": {"targets": targets("decision"), "cardinality": "many", "parts": True, "on_delete": "refuse"},
}

SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly.\n"},
]
AGAIN = [SECTIONS[0], {"title": "Rationale", "body": "Costs now move daily.\n"}]
OPTIONS = [{"title": "Keep weekly", "body": "Review every Monday."}, {"title": "Go monthly", "body": "Monthly."}]
LINKER = iri("decision", "price-reviews-happen-weekly")
TARGET = iri("decision", "prices-are-reviewed-monthly")
OTHER = iri("decision", "prices-are-reviewed-yearly")
ROLLBACK = f"{TARGET}#options/rollback"
WAITING = [(TARGET, [(LINKER, "supersedes", "supersedes", "options/rollback")])]
LINKER_CONTENT = {"supersedes": ROLLBACK, "sections": SECTIONS, "options": OPTIONS}


def _a_decision_waiting_on_an_option_its_target_was_created_without(root):
    """A client over a store holding a decision that supersedes the option "rollback" of a second decision, the
    second created afterwards with no such option, and a third decision nothing links to."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, LINKING_TYPE)
    for title, content in (
        ("Price reviews happen weekly", LINKER_CONTENT),
        ("Prices are reviewed monthly", {"sections": SECTIONS, "options": OPTIONS}),
        ("Prices are reviewed yearly", {"sections": SECTIONS}),
    ):
        made = request(client, "decision", title, content)
        assert not made.faults, made.faults
    assert _listed(placeholders(client)) == WAITING
    return client


def _listed(asked):
    assert not asked.faults, asked.faults
    return [
        (each.id, [(link.artifact, link.field, link.place, link.part) for link in each.links])
        for each in asked.placeholders
    ]


LEAVING_THE_LINK = {
    "the whole replaced": lambda client: replace(client, LINKER, {**LINKER_CONTENT, "sections": AGAIN}),
    "a section replaced": lambda client: replace(client, LINKER, AGAIN[1], path="sections/rationale"),
    "an option replaced": lambda client: replace(
        client, LINKER, {"title": "Keep weekly", "body": "Review every Friday."}, path="options/keep-weekly",
    ),
    "the field replaced with what it held": lambda client: replace(client, LINKER, ROLLBACK, path="supersedes"),
    "an option added": lambda client: add(client, LINKER, "options", {"title": "Go daily"}),
    "an option removed": lambda client: replace(client, LINKER, OPTIONS[:1], path="options"),
    "another link added that lands": lambda client: replace(client, LINKER, {**LINKER_CONTENT, "builds_on": [OTHER]}),
    "a set of replacements": lambda client: replace_many(client, [
        replaced(LINKER, {**LINKER_CONTENT, "sections": AGAIN}), replaced(OTHER, {"sections": AGAIN}),
    ]),
    "a set of options added": lambda client: add_many(client, [
        added(LINKER, "options", {"title": "Go daily"}), added(LINKER, "options", {"title": "Go yearly"}),
    ]),
}


@pytest.mark.parametrize("change", sorted(LEAVING_THE_LINK))
def test_a_change_that_leaves_a_link_waiting_on_a_part_its_target_lacks_lands_and_the_link_still_waits(root, change):
    client = _a_decision_waiting_on_an_option_its_target_was_created_without(root)
    before = held.text(root, LINKER)
    changed = LEAVING_THE_LINK[change](client)
    assert not changed.faults, changed.faults
    assert held.text(root, LINKER) != before
    assert held.artifact(root, LINKER)["supersedes"] == ROLLBACK
    assert _listed(placeholders(client)) == WAITING
    checked = check(client)
    assert (list(checked.violations), _listed(checked)) == ([], WAITING)
    assert [each.id for each in read(client, LINKER).placeholders] == [TARGET]


ALTERING_OR_ADDING = {
    "its part altered to another the target lacks": (
        lambda client: replace(client, LINKER, {**LINKER_CONTENT, "supersedes": f"{TARGET}#options/go-yearly"}),
        ["supersedes"],
    ),
    "its part altered by replacing the field": (
        lambda client: replace(client, LINKER, f"{TARGET}#options/go-yearly", path="supersedes"), ["supersedes"],
    ),
    "its target altered to another that lacks the part": (
        lambda client: replace(client, LINKER, {**LINKER_CONTENT, "supersedes": f"{OTHER}#options/rollback"}),
        ["supersedes"],
    ),
    "a second link added into the part the first waits on": (
        lambda client: replace(client, LINKER, {**LINKER_CONTENT, "builds_on": [ROLLBACK]}), ["builds_on/0"],
    ),
    "a second link added into another part the target lacks": (
        lambda client: replace(client, LINKER, {**LINKER_CONTENT, "builds_on": [OTHER, f"{TARGET}#options/go-yearly"]}),
        ["builds_on/1"],
    ),
    "the same link written in another artifact": (
        lambda client: replace(client, OTHER, {"supersedes": ROLLBACK, "sections": SECTIONS}), ["supersedes"],
    ),
    "the same link written in a new artifact": (
        lambda client: request(client, "decision", "Prices are reviewed daily", {
            "supersedes": ROLLBACK, "sections": SECTIONS,
        }),
        ["supersedes"],
    ),
    "a set one of whose replacements adds a second link": (
        lambda client: replace_many(client, [
            replaced(OTHER, {"sections": AGAIN}), replaced(LINKER, {**LINKER_CONTENT, "builds_on": [ROLLBACK]}),
        ]),
        ["builds_on/0"],
    ),
}


@pytest.mark.parametrize("change", sorted(ALTERING_OR_ADDING))
def test_a_link_a_change_adds_or_alters_into_a_part_a_held_artifact_lacks_is_refused_while_the_first_waits(root, change):
    client = _a_decision_waiting_on_an_option_its_target_was_created_without(root)
    before = [held.text(root, each) for each in (LINKER, TARGET, OTHER)]
    attempt, places = ALTERING_OR_ADDING[change]
    refused = attempt(client)
    assert [(fault.rule, fault.place) for fault in refused.faults] == [("ref", place) for place in places]
    assert [held.text(root, each) for each in (LINKER, TARGET, OTHER)] == before
    assert _listed(placeholders(client)) == WAITING
    assert list(check(client).violations) == []


def test_a_link_that_waited_and_was_altered_away_is_new_when_it_is_written_again(root):
    client = _a_decision_waiting_on_an_option_its_target_was_created_without(root)
    assert not replace(client, LINKER, {"sections": SECTIONS, "options": OPTIONS}).faults
    assert _listed(placeholders(client)) == []
    refused = replace(client, LINKER, LINKER_CONTENT)
    assert [(fault.rule, fault.place) for fault in refused.faults] == [("ref", "supersedes")]


GAINING = replacing(TARGET, {"sections": SECTIONS, "options": [*OPTIONS, {"title": "Rollback"}]})
KEEPING = replacing(LINKER, AGAIN[1], path="sections/rationale")


@pytest.mark.parametrize("first, second", [(GAINING, KEEPING), (KEEPING, GAINING)], ids=[
    "the target gains the part first", "the linker changes first",
])
def test_a_change_keeping_the_link_and_its_target_gaining_the_part_made_at_once_both_land(root, first, second):
    client = _a_decision_waiting_on_an_option_its_target_was_created_without(root)

    def landing_first():
        landed = client.Replace(first)
        assert landed.WhichOneof("outcome") == "result", landed

    landed = at_once.landed_second(at_once.OnAThread(root, "Replace", second), landing_first)
    assert not landed.faults, landed.faults
    assert held.artifact(root, LINKER)["sections"][1]["body"] == "Costs now move daily.\n"
    assert _listed(placeholders(client)) == []
    assert list(check(client).violations) == []
    refused = replace(client, TARGET, {"sections": SECTIONS, "options": OPTIONS})
    assert [fault.rule for fault in refused.faults] == ["on_delete"], refused.faults


def test_a_change_keeping_the_link_drafted_before_its_target_was_created_without_the_part_lands(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, LINKING_TYPE)
    assert not request(client, "decision", "Price reviews happen weekly", LINKER_CONTENT).faults

    def landing_first():
        made = request(client, "decision", "Prices are reviewed monthly", {"sections": SECTIONS, "options": OPTIONS})
        assert not made.faults, made.faults

    landed = at_once.landed_second(at_once.OnAThread(root, "Replace", KEEPING), landing_first)
    assert not landed.faults, landed.faults
    assert _listed(placeholders(client)) == WAITING
    assert list(check(client).violations) == []


def test_removing_the_target_of_a_link_that_waits_on_a_part_of_it_is_refused_and_the_linker_still_changes(root):
    client = _a_decision_waiting_on_an_option_its_target_was_created_without(root)
    refused = remove(client, TARGET)
    assert [(fault.rule, fault.artifact) for fault in refused.faults] == [("on_delete", LINKER)], refused.faults
    assert not replace(client, LINKER, AGAIN[1], path="sections/rationale").faults
    assert _listed(placeholders(client)) == WAITING


def test_kb_validate_says_of_a_link_that_waits_what_it_said_before_its_artifact_changed(root):
    client = _a_decision_waiting_on_an_option_its_target_was_created_without(root)
    before = _kb("validate", cwd=root, env={})
    assert (before.returncode, before.stderr) == (0, "")
    assert before.stdout.splitlines() == [f"placeholder\t{ROLLBACK}\t{LINKER}\tsupersedes"]
    assert not replace(client, LINKER, AGAIN[1], path="sections/rationale").faults
    after = _kb("validate", cwd=root, env={})
    assert (after.returncode, after.stderr, after.stdout) == (0, "", before.stdout)
