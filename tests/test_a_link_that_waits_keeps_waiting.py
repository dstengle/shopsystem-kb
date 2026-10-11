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
from conftest import OPERATOR, _kb, exported
from kb import client as kb_client

LINKING_TYPE = copy.deepcopy(DECISION_TYPE)
LINKING_TYPE["schema"]["properties"]["supersedes"]["ref"]["parts"] = True
LINKING_TYPE["schema"]["properties"]["builds_on"] = {
    "type": "array",
    "items": {"type": "string"},
    "ref": {"targets": targets("decision"), "cardinality": "many", "parts": True, "on_delete": "refuse"},
}
LINKING_TYPE["schema"]["parts"]["options"]["items"]["properties"]["replaces"] = {
    "type": "string",
    "ref": {"targets": targets("decision"), "cardinality": "one", "parts": True, "on_delete": "refuse"},
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


def _a_decision_waiting_on_an_option_its_target_was_created_without(root, content=LINKER_CONTENT, waiting=WAITING):
    """A client over a store holding a decision that supersedes the option "rollback" of a second decision, or links
    to it as the content given does, the second created afterwards with no such option, and a third decision."""
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, LINKING_TYPE)
    for title, content in (
        ("Price reviews happen weekly", content),
        ("Prices are reviewed monthly", {"sections": SECTIONS, "options": OPTIONS}),
        ("Prices are reviewed yearly", {"sections": SECTIONS}),
    ):
        made = request(client, "decision", title, content)
        assert not made.faults, made.faults
    assert _listed(placeholders(client)) == waiting
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


# decision 14 of batch 35: the link is told by the thing holding it, the artifact or the item of that name, its
# field, the IRI and the part, never by where it stands in a list.
FIRST, THIRD = {"id": "first", "title": "First"}, {"id": "third", "title": "Third"}
SECOND = {"id": "second", "title": "Second", "replaces": ROLLBACK}
BARE = {"id": "second", "title": "Second"}
IN_AN_ITEM = {"sections": SECTIONS, "options": [FIRST, SECOND, THIRD]}
IN_A_LIST = {"sections": SECTIONS, "builds_on": [OTHER, ROLLBACK]}
HELD_BY = {"an item": (IN_AN_ITEM, "replaces", "options/1/replaces"), "a list": (IN_A_LIST, "builds_on", "builds_on/1")}


def _waiting_at(field, place):
    return [(TARGET, [(LINKER, field, place, "options/rollback")])]


def _a_decision_whose_link_waits_in(root, holder):
    """The client, with the linker's link held in the second of its options, or second in a field of several."""
    content, field, place = HELD_BY[holder]
    return _a_decision_waiting_on_an_option_its_target_was_created_without(root, content, _waiting_at(field, place))


LEAVING_THE_LINK_WHERE_IT_IS_HELD = {
    "the first option removed": ("an item", lambda client: replace(client, LINKER, [SECOND, THIRD], path="options"), 0),
    "the first option removed by replacing the whole": (
        "an item", lambda client: replace(client, LINKER, {**IN_AN_ITEM, "options": [SECOND, THIRD]}), 0,
    ),
    "the options reordered": ("an item", lambda client: replace(client, LINKER, [THIRD, FIRST, SECOND], path="options"), 2),
    "an option put before it": (
        "an item", lambda client: replace(client, LINKER, [{"title": "Zeroth"}, FIRST, SECOND, THIRD], path="options"), 2,
    ),
    "a later option removed": ("an item", lambda client: replace(client, LINKER, [FIRST, SECOND], path="options"), 1),
    "the option holding it replaced with the same link": (
        "an item", lambda client: replace(client, LINKER, {**SECOND, "body": "Said again."}, path="options/second"), 1,
    ),
    "the first link of the field removed": ("a list", lambda client: replace(client, LINKER, {**IN_A_LIST, "builds_on": [ROLLBACK]}), 0),
    "the links of the field reordered": (
        "a list", lambda client: replace(client, LINKER, {**IN_A_LIST, "builds_on": [ROLLBACK, OTHER]}), 0,
    ),
}


@pytest.mark.parametrize("change", sorted(LEAVING_THE_LINK_WHERE_IT_IS_HELD))
def test_a_change_to_what_stands_beside_a_link_that_waits_lands_wherever_it_leaves_the_link_standing(root, change):
    holder, attempt, index = LEAVING_THE_LINK_WHERE_IT_IS_HELD[change]
    client = _a_decision_whose_link_waits_in(root, holder)
    _, field, place = HELD_BY[holder]
    place = place.replace("1", str(index))
    still = _waiting_at(field, place)
    before = held.text(root, LINKER)
    changed = attempt(client)
    assert not changed.faults, changed.faults
    assert held.text(root, LINKER) != before
    assert _listed(placeholders(client)) == still
    checked = check(client)
    assert (list(checked.violations), _listed(checked)) == ([], still)
    assert [each.id for each in read(client, LINKER).placeholders] == [TARGET]
    validated = _kb("validate", cwd=root, env={})
    assert (validated.returncode, validated.stdout) == (0, f"placeholder\t{ROLLBACK}\t{LINKER}\t{place}\n")


MOVING_OR_ALTERING = {
    "moved to another option": (
        "an item", lambda client: replace(client, LINKER, [{**FIRST, "replaces": ROLLBACK}, BARE, THIRD], path="options"),
        "options/0/replaces",
    ),
    "left in an option of another name": (
        "an item", lambda client: replace(client, LINKER, [FIRST, {"title": "Second again", "replaces": ROLLBACK}], path="options"),
        "options/1/replaces",
    ),
    "moved out of its option to a field of the decision": (
        "an item", lambda client: replace(client, LINKER, {**IN_AN_ITEM, "options": [FIRST, BARE], "supersedes": ROLLBACK}),
        "supersedes",
    ),
    "its part altered inside its option": (
        "an item", lambda client: replace(
            client, LINKER, {**BARE, "replaces": f"{TARGET}#options/go-yearly"}, path="options/second",
        ),
        "options/1/replaces",
    ),
    "written again in another option as the first is removed": (
        "an item", lambda client: replace(client, LINKER, [SECOND, {**THIRD, "replaces": ROLLBACK}], path="options"),
        "options/1/replaces",
    ),
    "written a second time in its field": (
        "a list", lambda client: replace(client, LINKER, {**IN_A_LIST, "builds_on": [ROLLBACK, ROLLBACK]}), "builds_on/1",
    ),
    "its part altered in its field": (
        "a list", lambda client: replace(client, LINKER, {**IN_A_LIST, "builds_on": [OTHER, f"{TARGET}#options/go-yearly"]}),
        "builds_on/1",
    ),
    "moved to another field": (
        "a list", lambda client: replace(client, LINKER, {"sections": SECTIONS, "builds_on": [OTHER], "supersedes": ROLLBACK}),
        "supersedes",
    ),
}


@pytest.mark.parametrize("change", sorted(MOVING_OR_ALTERING))
def test_a_link_that_waits_moved_to_another_holder_or_altered_where_it_is_held_is_refused_as_new(root, change):
    holder, attempt, place = MOVING_OR_ALTERING[change]
    client = _a_decision_whose_link_waits_in(root, holder)
    before = held.text(root, LINKER)
    refused = attempt(client)
    assert [(fault.rule, fault.place) for fault in refused.faults] == [("ref", place)]
    assert held.text(root, LINKER) == before
    assert _listed(placeholders(client)) == _waiting_at(*HELD_BY[holder][1:])
    assert list(check(client).violations) == []


# An item whose file gave it no name, which an import names as a write does, and whose link into it waits all the same.
def _imported(directory, root, tmp_path):
    assert _kb("init", str(root), cwd=tmp_path, env={"KB_ACTOR": OPERATOR}).returncode == 0
    return _kb("import", str(directory), cwd=root, env={"KB_ACTOR": OPERATOR})


def _seeded(directory, root, tmp_path):
    return _kb("init", str(root), "--seed", str(directory), cwd=tmp_path, env={"KB_ACTOR": OPERATOR})


def _a_decision_whose_link_waits_in_an_option_with_no_name(tmp_path, landed):
    """A client over a store made from a directory of files, as `landed` lands it, in which the second option of a
    decision carries no `id` and holds a link into the option "rollback" of a second decision, the second created
    afterwards with no such option."""
    def fill(client):
        define(client, LINKING_TYPE)
        assert not request(client, "decision", "Price reviews happen weekly", IN_AN_ITEM).faults

    directory = exported(tmp_path, fill)
    (file,) = [each for each in directory.rglob("*.yaml") if "id: second\n" in each.read_text()]
    file.write_text(file.read_text().replace("id: second\n    title: Second", "title: Second", 1))
    root = tmp_path / "landed"
    root.mkdir()
    ran = landed(directory, root, tmp_path)
    assert (ran.returncode, ran.stderr) == (0, ""), ran.stderr
    client = kb_client.connect(root)
    assert held.artifact(root, LINKER)["options"][1]["id"] == "second"
    assert not request(client, "decision", "Prices are reviewed monthly", {"sections": SECTIONS, "options": OPTIONS}).faults
    return root, client


LANDED = pytest.mark.parametrize("landed", [_imported, _seeded], ids=["imported", "seeded"])
NO_NAME = _waiting_at("replaces", "options/1/replaces")


def _says_the_link_waits(root, client):
    """The placeholders rpc, the store's check and `kb validate` each list the link, and nothing is violated."""
    assert _listed(placeholders(client)) == NO_NAME
    checked = check(client)
    assert (list(checked.violations), _listed(checked)) == ([], NO_NAME)
    validated = _kb("validate", cwd=root, env={})
    assert (validated.returncode, validated.stdout) == (0, f"placeholder\t{ROLLBACK}\t{LINKER}\toptions/1/replaces\n")


@LANDED
def test_a_link_that_waits_in_an_item_with_no_name_still_waits_once_its_target_is_created_without_the_part(tmp_path, landed):
    _says_the_link_waits(*_a_decision_whose_link_waits_in_an_option_with_no_name(tmp_path, landed))


@LANDED
def test_a_change_that_leaves_a_link_waiting_in_an_item_with_no_name_lands_and_the_link_still_waits(tmp_path, landed):
    root, client = _a_decision_whose_link_waits_in_an_option_with_no_name(tmp_path, landed)
    before = held.text(root, LINKER)
    changed = replace(client, LINKER, AGAIN[1], path="sections/rationale")
    assert not changed.faults, changed.faults
    assert held.text(root, LINKER) != before
    assert held.artifact(root, LINKER)["options"][1]["replaces"] == ROLLBACK
    _says_the_link_waits(root, client)
