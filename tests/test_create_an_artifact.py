import copy
import re

from pytest_bdd import given, parsers, scenario, then, when

from calls import (
    DECISION_TYPE, MISORDERED_DECISION, ORDERED_DECISION_TYPE, PROCESS_TYPE, READING_ORDER, TYPE_OF_TYPES, check, create,
    define, iri, next_version, placeholders, read, refs, remove, replace, request, slug, start_a_store, type_iri,
    version_iri,
)
import held
from kb import content, client as kb_client
from kb.contract import kb_pb2


@scenario("change-the-store.feature", "The client creates an artifact, giving its IRI and the IRI of the version of its type it conforms to")
def test_the_client_creates_an_artifact_giving_its_iri_and_the_iri_of_the_version_of_its():
    pass


@scenario("check-a-change.feature", "An artifact created naming a version of its type is checked against that version")
def test_an_artifact_created_naming_a_version_of_its_type_is_checked_against_that_version():
    pass


@scenario("check-a-change.feature", "An artifact pointing at an IRI the store does not hold, under a type it holds that the link allows, lands its link on a placeholder")
def test_an_artifact_pointing_at_an_iri_the_store_does_not_hold_under_a_type_it_holds_tha():
    pass


@scenario("check-a-change.feature", "An artifact pointing at an IRI the store does not hold, under a type the link does not allow, is refused")
def test_an_artifact_pointing_at_an_iri_the_store_does_not_hold_under_a_type_the_link_doe():
    pass


@scenario("check-a-change.feature", "An artifact pointing at an IRI under a type the store does not hold is refused")
def test_an_artifact_pointing_at_an_iri_under_a_type_the_store_does_not_hold_is_refused():
    pass


@scenario("check-a-change.feature", "An artifact pointing into a part a held artifact does not have is refused")
def test_an_artifact_pointing_into_a_part_a_held_artifact_does_not_have_is_refused():
    pass


@scenario("check-a-change.feature", "An artifact pointing into a part of an IRI the store does not hold, under a type it holds that the link allows, lands its link on a placeholder")
def test_an_artifact_pointing_into_a_part_of_an_iri_the_store_does_not_hold_under_a_type():
    pass


@scenario("check-a-change.feature", "Creating an artifact at an IRI links already point at fills the placeholder")
def test_creating_an_artifact_at_an_iri_links_already_point_at_fills_the_placeholder():
    pass


@scenario("check-a-change.feature", "Creating an artifact without the part a link points into leaves that link on a placeholder")
def test_creating_an_artifact_without_the_part_a_link_points_into_leaves_that_link_on_a_p():
    pass


@scenario("check-a-change.feature", "Changing an artifact that holds a link waiting on a part its target lacks leaves the link waiting")
def test_changing_an_artifact_that_holds_a_link_waiting_on_a_part_its_target_lacks_leaves():
    pass


@scenario("hand-over-content.feature", "Content given to a create that carries what travels beside it is refused")
def test_content_given_to_a_create_that_carries_what_travels_beside_it_is_refused():
    pass


@scenario('name-artifacts-and-items.feature', "A part given a name of the client's choosing on create holds that name")
def test_a_part_given_a_name_of_the_client_s_choosing_on_create_holds_that_name():
    pass


@scenario("name-artifacts-and-items.feature", "A part given no name on create is named by the store from its title or its place")
def test_a_part_given_no_name_on_create_is_named_by_the_store_from_its_title_or_its_place():
    pass


@scenario('name-artifacts-and-items.feature', "A part is named by its artifact's IRI, # and its place in it")
def test_a_part_is_named_by_its_artifact_s_iri_and_its_place_in_it():
    pass


@scenario("name-artifacts-and-items.feature", "A title given as the number 12 is still a title")
def test_a_title_given_as_the_number_12_is_still_a_title():
    pass


@scenario("name-artifacts-and-items.feature", "A title given as the yes-or-no true is still a title")
def test_a_title_given_as_the_yes_or_no_true_is_still_a_title():
    pass


@scenario('name-artifacts-and-items.feature', "An artifact created at an IRI not under its type's IRI is refused")
def test_an_artifact_created_at_an_iri_not_under_its_type_s_iri_is_refused():
    pass


@scenario('name-artifacts-and-items.feature', "An artifact created at an IRI of the client's choosing under its type's IRI is held at that IRI")
def test_an_artifact_created_at_an_iri_of_the_client_s_choosing_under_its_type_s_iri_is_h():
    pass


@scenario("name-artifacts-and-items.feature", "An artifact created at an IRI the store already holds an artifact at is refused")
def test_an_artifact_created_at_an_iri_the_store_already_holds_an_artifact_at_is_refused():
    pass


@scenario("name-artifacts-and-items.feature", "An artifact created giving a part a name that is not a plain name is refused")
def test_an_artifact_created_giving_a_part_a_name_that_is_not_a_plain_name_is_refused():
    pass


@scenario("name-artifacts-and-items.feature", "An artifact created giving two parts of one collection the same name is refused")
def test_an_artifact_created_giving_two_parts_of_one_collection_the_same_name_is_refused():
    pass


@scenario("name-artifacts-and-items.feature", "An artifact keeps the IRI it was created with for life")
def test_an_artifact_keeps_the_iri_it_was_created_with_for_life():
    pass


@scenario("name-what-is-asked-for.feature", "A create naming a type version the store does not hold is refused")
def test_a_create_naming_a_type_version_the_store_does_not_hold_is_refused():
    pass


@scenario('name-what-is-asked-for.feature', 'A create naming a version of a type not shaped as a type\'s IRI, "@" and a number is refused')
def test_a_create_naming_a_version_of_a_type_not_shaped_as_a_type_s_iri_and_a_number_is_r():
    pass


@scenario('name-what-is-asked-for.feature', "A name a call carries is an IRI of kb's grammar")
def test_a_name_a_call_carries_is_an_iri_of_kb_s_grammar():
    pass


@scenario("change-the-store.feature", "An artifact created without a title is refused")
def test_an_artifact_created_without_a_title_is_refused():
    pass


@scenario("check-a-change.feature", "An artifact missing a required section is refused")
def test_an_artifact_missing_a_required_section_is_refused():
    pass


@scenario("check-a-change.feature", "An artifact with several faults reports them all")
def test_an_artifact_with_several_faults_reports_them_all():
    pass


@scenario("check-a-change.feature", "Faults found by different rules all come back together")
def test_faults_found_by_different_rules_all_come_back_together():
    pass


@scenario(
    "check-a-change.feature",
    "An artifact refused with several faults has them given in the order its places stand when it reads back",
)
def test_an_artifact_refused_with_several_faults_has_them_in_reading_order():
    pass


@scenario("check-a-change.feature", "A section carrying anything besides its title, its body and its own sections is refused")
def test_a_section_carrying_anything_besides_its_title_its_body_and_its_own_sections_is_refused():
    pass


@scenario("check-a-change.feature", "A section with no title is refused")
def test_a_section_with_no_title_is_refused():
    pass


@scenario("check-a-change.feature", "A section with no body is refused")
def test_a_section_with_no_body_is_refused():
    pass


@scenario("check-a-change.feature", "A section whose body is empty is kept as it is")
def test_a_section_whose_body_is_empty_is_kept_as_it_is():
    pass


@scenario("hand-over-content.feature", "Content carrying a title of its own is refused")
def test_content_carrying_a_title_of_its_own_is_refused():
    pass


@scenario("hand-over-content.feature", "Content telling the store how to build a value is refused")
def test_content_telling_the_store_how_to_build_a_value_is_refused():
    pass


@scenario("hand-over-content.feature", "Content holding more than one document is refused")
def test_content_holding_more_than_one_document_is_refused():
    pass


@scenario("hand-over-content.feature", "A value that reads as a switch or as a clock time is still the text that was written")
def test_a_value_that_reads_as_a_switch_or_as_a_clock_time_is_still_the_text_that_was_written():
    pass


@scenario("hand-over-content.feature", "Content that writes a value once and points back at it elsewhere is refused")
def test_content_that_writes_a_value_once_and_points_back_at_it_elsewhere_is_refused():
    pass


@scenario("hand-over-content.feature", "Content that opens by declaring the format it is written in is refused")
def test_content_that_opens_by_declaring_the_format_it_is_written_in_is_refused():
    pass


@scenario("hand-over-content.feature", "Content naming the same entry twice is refused")
def test_content_naming_the_same_entry_twice_is_refused():
    pass


@scenario("hand-over-content.feature", "Values written as a yes-or-no, as nothing and as a number keep those meanings")
def test_values_written_as_a_yes_or_no_as_nothing_and_as_a_number_keep_those_meanings():
    pass


@scenario("hand-over-content.feature", "Content the store cannot make sense of is refused")
def test_content_the_store_cannot_make_sense_of_is_refused():
    pass


@scenario("hand-over-content.feature", "A field written as a bare date is the text that was written")
def test_a_field_written_as_a_bare_date_is_the_text_that_was_written():
    pass


@scenario("hand-over-content.feature", "Prose the store could not write back in its one form is refused")
def test_prose_the_store_could_not_write_back_in_its_one_form_is_refused():
    pass


@scenario("name-artifacts-and-items.feature", "A title that reads as a date is still a title")
def test_a_title_that_reads_as_a_date_is_still_a_title():
    pass


@scenario("name-artifacts-and-items.feature", "A title that reads as yes is still a title")
def test_a_title_that_reads_as_yes_is_still_a_title():
    pass


SECTIONS = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs move weekly, so a monthly review lags them.\n"},
]
OPTIONS = [
    {"title": "Keep weekly", "body": "Review every Monday."},
    {"title": "Go monthly", "body": "Review on the first of the month."},
]


@given(
    "a store holding a decision type, at its first version, whose artifacts require a purpose then a rationale, "
    "may link to the decision they supersede, and may carry a collection of options",
    target_fixture="client",
)
@given(
    "a store holding a decision type whose artifacts require a purpose then a rationale, "
    "may link to the decision they supersede, and may carry a collection of options",
    target_fixture="client",
)
def _store_with_decision_type(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    return client


@then("the client is given the name the artifact keeps for life and its first version")
def _given_name_and_first_version(created):
    assert created.id == iri("decision", "price-reviews-happen-weekly")
    assert created.revision == 1


@given(
    "a store holding two versions of the decision type, where the later one requires a section the earlier one does "
    "not",
    target_fixture="client",
)
def _store_with_two_versions_of_the_decision_type(root):
    client = _store_with_decision_type(root)
    assert not next_version(client, "decision", DECISION_TYPE, [*REQUIRED, "Consequences"]).faults
    return client


REQUIRED = [section["title"] for section in DECISION_TYPE["schema"]["sections"]]


@when(
    "the client creates a decision naming the earlier version of the decision type, with content that fits the "
    "earlier version and lacks the section the later one requires, saying which role and why",
    target_fixture="created",
)
def _create_naming_the_earlier_version(client):
    return request(client, "decision", "Price reviews happen weekly", {"sections": SECTIONS}, message="Record it", version=1)


@then("the client is given the IRI the artifact keeps for life and its first version")
def _given_iri_and_first_version(created):
    assert not created.faults, created.faults
    assert (created.id, created.revision) == (iri("decision", "price-reviews-happen-weekly"), 1)


CHOSEN = iri("decision", "pricing/weekly-reviews")


@given(parsers.parse('a store holding a decision type at "{type_iri}"'), target_fixture="client")
def _store_with_decision_type_at(root, before, type_iri):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE, at=type_iri)
    before.update(held=held.holds(root))
    return client


@when(parsers.parse('the client creates a decision at "{at}", saying which role and why'), target_fixture="created")
def _create_at(client, at):
    return request(client, "decision", "Price reviews happen weekly", {"sections": SECTIONS}, message="Record it", at=at)


@then(parsers.parse('the decision is held at "{at}"'))
def _decision_held_at(root, created, at):
    assert not created.faults, created.faults
    assert created.id == at
    assert held.holds_artifact(root, at)


@then("the artifact is rejected because an artifact's IRI sits under its type's IRI")
def _rejected_as_not_under_its_type(created):
    assert (created.id, created.revision) == ("", 0)
    assert [fault.rule for fault in created.faults] == ["identity"]
    assert created.faults[0].message.startswith("an artifact's IRI sits under its type's IRI")


@then(parsers.parse('the refusal names "{at}"'))
def _the_refusal_names(created, at):
    [fault] = created.faults
    assert fault.artifact == at
    assert repr(at) in fault.message


@given(parsers.parse('a decision the store holds at "{at}"'), target_fixture="already")
def _a_decision_held_at(client, at):
    """The decision as it reads once held, to compare with what it reads as later."""
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS}, at=at)
    return read(client, at, whole=True)


@when(
    parsers.parse('the client creates another decision at "{at}", saying which role and why'), target_fixture="created",
)
def _create_another_at(client, at):
    return request(client, "decision", "Price reviews happen monthly", {"sections": SECTIONS}, message="Slow down", at=at)


@then("the artifact is rejected because an IRI names one artifact")
def _rejected_as_already_held(created):
    assert (created.id, created.revision) == ("", 0)
    assert [fault.rule for fault in created.faults] == ["identity"]
    assert created.faults[0].message.startswith("an IRI names one artifact")


@then("the decision already there reads as it did, at the revision it held")
def _already_there_as_it_was(client, already):
    assert already.revision == 1
    assert read(client, already.id, whole=True) == already


REVISED = [
    {"title": "Purpose", "body": "Keep prices in step with costs.\n"},
    {"title": "Rationale", "body": "Costs now move daily, and weekly is what the shop can staff.\n"},
]


@given(parsers.parse('a decision the store holds at "{at}", changed several times since it was created'))
def _a_decision_changed_several_times(client, at):
    create(client, "decision", {"title": "Price reviews happen weekly", "sections": SECTIONS}, at=at)
    for sections in (REVISED, SECTIONS, REVISED):
        assert not replace(client, at, {"sections": sections}).faults


@when(parsers.parse('the client reads the decision at "{at}"'), target_fixture="shown")
def _read_the_decision_at(client, at):
    return {"at": at, "read": read(client, at, whole=True)}


@then("the client is given the decision, at its latest revision")
def _given_at_its_latest_revision(shown):
    given = shown["read"]
    assert not given.faults, given.faults
    assert (given.id, given.revision) == (shown["at"], 4)
    assert given.content == content.dumps({"sections": REVISED})


@then("the store made up no other IRI for it")
def _no_other_iri(root, created):
    assert held.names(root) == sorted([TYPE_OF_TYPES, type_iri("decision"), created.id])


@when(
    "the client creates a decision, giving the IRI it chose for it, the IRI of that version of the decision type, a "
    "title, both required sections and two options, saying which role and why",
    target_fixture="created",
)
def _create_at_a_chosen_iri(client):
    """The options written before the sections, so the order the type declares is not the order written."""
    return request(
        client, "decision", "Price reviews happen weekly", {"options": OPTIONS, "sections": SECTIONS},
        message="Move price reviews to weekly", at=CHOSEN, version=1,
    )


@then("the client is given the IRI it chose and the decision's first revision")
def _given_the_chosen_iri_and_first_revision(created):
    assert not created.faults, created.faults
    assert (created.id, created.revision) == (CHOSEN, 1)


@then("the store holds the decision at that IRI")
def _held_at_that_iri(root):
    assert held.holds_artifact(root, CHOSEN)


@then("the decision records that version of the decision type")
def _records_that_version(client):
    assert read(client, CHOSEN).type == version_iri("decision", 1)


@then("reading it back gives what was written, in the order that version declares")
def _reads_back_in_declared_order(client):
    named_options = [{"id": "keep-weekly", **OPTIONS[0]}, {"id": "go-monthly", **OPTIONS[1]}]
    assert read(client, CHOSEN, whole=True).content == content.dumps({"sections": SECTIONS, "options": named_options})


@when(
    "the client creates a decision whose content carries a title as well as the title given alongside it, "
    "saying which role and why",
    target_fixture="refused",
)
def _create_with_a_title_inside(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "title": "Price reviews, weekly",
        "sections": SECTIONS,
    }, message="Move price reviews to weekly")


@then(
    "the artifact is rejected because a title is given alongside the content, never inside it, "
    "and the title the content carried is named back"
)
def _rejected_for_a_title_inside(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.place, fault.rule) for fault in refused.faults] == [("title", "identity")]
    assert "Price reviews, weekly" in refused.faults[0].message


CARRIED_BESIDE = {"id": iri("decision", "price-reviews-happen-weekly"), "type": version_iri("decision", 3), "revision": 7}


@when(
    "the client creates a decision whose content carries the artifact's IRI, the version of its type and a revision "
    "for the artifact itself, saying which role and why",
    target_fixture="refused",
)
def _create_with_what_travels_beside_inside(client):
    return request(client, "decision", "Price reviews happen weekly", {
        **CARRIED_BESIDE, "sections": SECTIONS,
    }, message="Move price reviews to weekly")


@then("the artifact is rejected because content holds only what the type declares")
def _rejected_for_what_travels_beside(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.place, fault.rule) for fault in refused.faults] == [(key, "identity") for key in CARRIED_BESIDE]


@then("the artifact's IRI, the version of its type and the revision the content carried are each named back")
def _each_carried_named_back(refused):
    for fault, value in zip(refused.faults, CARRIED_BESIDE.values(), strict=True):
        assert str(value) in fault.message


@when(parsers.parse('the client creates a decision titled "{title}", saying which role and why'), target_fixture="created")
def _create_titled(client, title):
    return request(client, "decision", title, {"sections": SECTIONS}, message="Record it")


@then("the title reads back as the text that was written, not as a date")
def _title_is_text_not_a_date(root, client, created):
    assert read(client, created.id).title == "2026-09-24"
    on_disk = held.artifact(root, created.id)
    assert on_disk["title"] == "2026-09-24"


@when(
    "the client creates a decision with both required sections and no title, saying which role and why",
    target_fixture="refused",
)
def _create_without_a_title(client):
    return request(client, "decision", "", {"sections": SECTIONS}, message="Record it", at=iri("decision", "untitled"))


@then("the artifact is rejected because an artifact cannot be created without a title")
def _rejected_without_a_title(refused):
    assert [(fault.place, fault.rule, fault.message) for fault in refused.faults] == [
        ("title", "title", "an artifact cannot be created without a title"),
    ]


@then("the title reads back as the text that was written, not as a yes or a no")
def _title_is_text_not_a_bool(root, client, created):
    assert read(client, created.id).title == "yes"
    on_disk = held.artifact(root, created.id)
    assert on_disk["title"] == "yes"


def _raw(client, text):
    """A Create whose content is sent as written, so the text can carry what dumps never writes."""
    return request(client, "decision", "Price reviews happen weekly", text, message="Record it")


@when("the client creates a decision whose content carries a tag on one of its values, saying which role and why", target_fixture="refused")
def _create_with_a_tag(client):
    return _raw(client, "sections:\n  - title: Purpose\n    body: !!binary aGVsbG8=\n  - title: Rationale\n    body: Why.\n")


@then("the artifact is rejected because content is read plainly as written and carries no tags")
def _rejected_for_a_tag(refused):
    assert [(fault.rule, fault.message) for fault in refused.faults] == [
        ("content", "content is read plainly as written and carries no tags"),
    ]


@when(
    "the client creates a decision from content holding two documents one after the other, saying which role and why",
    target_fixture="refused",
)
def _create_from_two_documents(client):
    one = "sections:\n  - title: Purpose\n    body: Why.\n  - title: Rationale\n    body: Because.\n"
    return _raw(client, one + "---\n" + one)


@then("the artifact is rejected because content holds exactly one document")
def _rejected_for_two_documents(refused):
    assert [(fault.rule, fault.message) for fault in refused.faults] == [
        ("content", "content holds exactly one document"),
    ]


@when(
    "the client creates a decision whose purpose carries an extra entry of its own besides its title, its body "
    "and the sections inside it, saying which role and why",
    target_fixture="refused",
)
def _create_with_an_extra_entry_in_a_section(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "sections": [{**SECTIONS[0], "author": "shopkeeper"}, SECTIONS[1]],
    }, message="Record it")


@then(
    "the artifact is rejected because a section holds exactly its title, its body and the sections inside it, "
    "and the extra entry is named"
)
def _rejected_for_an_extra_entry(refused):
    assert [(fault.place, fault.rule) for fault in refused.faults] == [("sections/0", "additionalProperties")]
    assert "'author'" in refused.faults[0].message


@when(
    'the client creates a decision carrying one field written "on" and another written "1:20", saying which role and why',
    target_fixture="created",
)
def _create_with_values_yaml_1_1_would_convert(client):
    return _raw(client, (
        "switch: on\n"
        "time: 1:20\n"
        "sections:\n"
        "  - title: Purpose\n    body: Why.\n"
        "  - title: Rationale\n    body: Because.\n"
    ))


@then(
    "both fields read back as the text that was written, the first not as a yes or a no "
    "and the second not as a number"
)
def _both_fields_are_text(root, created):
    assert not created.faults, created.faults
    on_disk = held.artifact(root, created.id)
    assert (on_disk["switch"], on_disk["time"]) == ("on", "1:20")


@when(
    "the client creates a decision whose content writes a value once and points back at it from another place "
    "instead of writing it again, saying which role and why",
    target_fixture="refused",
)
def _create_with_an_alias(client):
    return _raw(client, (
        "reviewed: &day Monday\n"
        "decided: *day\n"
        "sections:\n"
        "  - title: Purpose\n    body: Why.\n"
        "  - title: Rationale\n    body: Because.\n"
    ))


@then(
    "the artifact is rejected because content is read exactly as written and nothing in it stands in "
    "for a value written somewhere else"
)
def _rejected_for_an_alias(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.rule, fault.message) for fault in refused.faults] == [
        ("content", "content is read exactly as written and nothing in it stands in for a value written somewhere else"),
    ]


@when(
    "the client creates a decision whose first section carries a body and no title, saying which role and why",
    target_fixture="refused",
)
def _create_with_a_section_without_a_title(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "sections": [{"body": SECTIONS[0]["body"]}, SECTIONS[1]],
    }, message="Record it")


@when(
    "the client creates a decision whose purpose carries a title and no body, saying which role and why",
    target_fixture="refused",
)
def _create_with_a_section_without_a_body(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "sections": [{"title": "Purpose"}, SECTIONS[1]],
    }, message="Record it")


@then(
    "the artifact is rejected because a section carries both a title and a body, and a section without one "
    "does not fit its type like anything else that does not"
)
def _rejected_for_a_section_missing_a_key(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.place, fault.rule) for fault in refused.faults] == [("sections/0", "required")]


@then("nothing is looked up or written anywhere, inside the store or outside it")
def _nothing_written_anywhere(attempt):
    assert attempt["after"] == attempt["before"]


@given("a title for a new decision that is the yes-or-no true rather than text", target_fixture="title")
def _a_title_that_is_a_yes_or_no():
    return True


@when("the client creates a decision with that title, saying which role and why", target_fixture="created")
def _create_with_that_title(client, title):
    return request(client, "decision", content.text(title), {"sections": SECTIONS}, message="Record it")


@then(parsers.parse('the title reads back as the text "{text}"'))
def _title_reads_back_as(root, client, created, text):
    assert not created.faults, created.faults
    assert read(client, created.id).title == text
    on_disk = held.artifact(root, created.id)
    assert on_disk["title"] == text


@given("content for a decision that names the same entry twice in the same place", target_fixture="written")
def _content_naming_an_entry_twice():
    return (
        "sections:\n"
        "  - title: Purpose\n"
        "    body: Keep prices in step with costs.\n"
        "    body: Keep prices low.\n"
        "  - title: Rationale\n"
        "    body: Because.\n"
    )


@when("the client creates a decision from that content, saying which role and why", target_fixture="created")
def _create_from_that_content(client, written):
    return _raw(client, written)


@then("the artifact is rejected because an entry is named once and only once, and the place the second one stands is named")
def _rejected_for_an_entry_named_twice(created):
    assert (created.id, created.revision) == ("", 0)
    assert [(fault.place, fault.rule) for fault in created.faults] == [("sections/0/body", "content")]
    assert created.faults[0].message.startswith("an entry is named once and only once")
    assert "line 4" in created.faults[0].message


@given(
    "content for a decision that opens with a line declaring which version of the writing format the rest is in",
    target_fixture="written",
)
def _content_opening_with_a_directive():
    return (
        "%YAML 1.1\n"
        "---\n"
        "switch: on\n"
        "sections:\n"
        "  - title: Purpose\n    body: Why.\n"
        "  - title: Rationale\n    body: Because.\n"
    )


@then(
    "the artifact is rejected because content is read plainly as written and opens with no declaration of its format, "
    "and the place the declaration stands is named"
)
def _rejected_for_a_directive(created):
    assert (created.id, created.revision) == ("", 0)
    assert [fault.rule for fault in created.faults] == ["content"]
    assert created.faults[0].message == (
        "content is read plainly as written and opens with no declaration of its format; "
        "line 1 declares %YAML 1.1"
    )


@given(parsers.parse('a store that holds no type for the kind "{kind}"'))
def _no_type_for_the_kind(root, kind):
    assert not held.holds_artifact(root, type_iri(kind))


UNHELD = {
    "the decision type at its second version, which the store does not hold": ("decision", 2),
    "the invoice type at its first version": ("invoice", 1),
}


@when(
    parsers.re(
        f"the client creates an artifact naming (?P<version>{'|'.join(map(re.escape, UNHELD))}), with a title and both "
        "required sections, saying which role and why"
    ),
    target_fixture="attempt",
)
def _create_naming_a_version_not_held(client, tmp_path, version):
    kind, number = UNHELD[version]
    before = held.everything_in(tmp_path)
    response = request(
        client, kind, "Price reviews happen weekly", {"sections": SECTIONS}, message="Record it", version=number,
    )
    return {
        "response": response, "before": before, "after": held.everything_in(tmp_path),
        "version": version_iri(kind, number),
    }


@then(
    "the artifact is rejected because a create names a version of a type the store holds, and the version asked for "
    "is given back"
)
def _rejected_for_a_version_not_held(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert [fault.rule for fault in refused.faults] == ["version"]
    assert refused.faults[0].message.startswith("a create names a version of a type the store holds")
    assert repr(attempt["version"]) in refused.faults[0].message


@then("that fault stands on its own, apart from anything wrong with the content")
def _the_version_fault_alone(attempt):
    assert [(fault.place, fault.rule) for fault in attempt["response"].faults] == [("", "version")]


@then("nothing is written anywhere in the store")
def _nothing_written_in_the_store(attempt):
    assert attempt["after"] == attempt["before"]


@given(
    'content for a decision carrying one field written "true", one field left as nothing, and one field written "12.5"',
    target_fixture="written",
)
def _content_with_typed_values():
    return (
        "urgent: true\n"
        "owner:\n"
        "weight: 12.5\n"
        "sections:\n"
        "  - title: Purpose\n    body: Why.\n"
        "  - title: Rationale\n    body: Because.\n"
    )


@then("the first field reads back as a yes-or-no, the second as nothing at all, and the third as a number")
def _typed_values_read_back(root, created):
    assert not created.faults, created.faults
    on_disk = held.artifact(root, created.id)
    assert (on_disk["urgent"], on_disk["owner"], on_disk["weight"]) == (True, None, 12.5)


@then("none of the three reads back as text")
def _none_of_them_text(root, created):
    on_disk = held.artifact(root, created.id)
    assert not any(isinstance(on_disk[name], str) for name in ("urgent", "owner", "weight"))


@given("a title for a new decision that is the number 12 rather than text", target_fixture="title")
def _a_title_that_is_a_number():
    return 12


@when(
    "the client creates a decision that is missing its purpose and supersedes a decision the store does not hold, "
    "saying which role and why",
    target_fixture="attempt",
)
def _create_with_two_faults(client, tmp_path):
    before = held.everything_in(tmp_path)
    response = request(client, "decision", "Price reviews happen weekly", {
        "supersedes": iri("decision", "prices-are-reviewed-monthly"),
        "sections": [SECTIONS[1]],
    }, message="Record it")
    return {
        "response": response, "before": before, "after": held.everything_in(tmp_path),
        "faults": [("sections", "sections"), ("supersedes", "ref")],
    }


@then("the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken")
def _rejected_with_both_faults(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert sorted((fault.artifact, fault.place, fault.rule) for fault in refused.faults) == [
        (iri("decision", "price-reviews-happen-weekly"), path, rule) for path, rule in attempt["faults"]
    ]


@then("the store is unchanged")
def _store_unchanged(attempt):
    assert attempt["after"] == attempt["before"]


TWICE = [
    {"title": "Keep weekly", "body": "Review every Monday."},
    {"title": "Keep weekly", "body": "Review every Monday, before opening."},
]


@when("the client creates a decision with a rationale and no purpose, saying which role and why", target_fixture="refused")
def _create_without_a_purpose(client):
    return request(client, "decision", "Price reviews happen weekly", {"sections": SECTIONS[1:]}, message="Record it")


@then("the artifact is rejected because the sections the type requires must all be present, in order")
def _rejected_for_the_sections(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.place, fault.rule) for fault in refused.faults] == [
        (iri("decision", "price-reviews-happen-weekly"), "sections", "sections"),
    ]
    assert refused.faults[0].message == (
        "the sections the type requires must all be present, in order; 'Purpose' is missing"
    )


@then("the artifact is rejected because a link must land on a node of a kind the type allows")
def _rejected_for_the_link(refused):
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.place, fault.rule) for fault in refused.faults] == [
        (iri("decision", "price-reviews-happen-weekly"), "supersedes", "ref"),
    ]
    assert refused.faults[0].message.startswith("a link must land on a node of a kind the type allows")


NOT_HELD = iri("decision", "prices-are-reviewed-monthly")


@when(
    "the client creates a decision that supersedes a decision the store does not hold, at an IRI under the decision "
    "type, saying which role and why",
    target_fixture="created",
)
def _create_superseding_a_decision_not_held(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "supersedes": NOT_HELD, "sections": SECTIONS,
    }, message="Record it")


@then("asked for the placeholders, the client is given that IRI, with the new decision linking to it")
def _the_placeholders_give_that_iri(client, created):
    asked = placeholders(client)
    assert not asked.faults, asked.faults
    assert [
        (each.id, [(link.artifact, link.field, link.place, link.part) for link in each.links])
        for each in asked.placeholders
    ] == [(NOT_HELD, [(created.id, "supersedes", "supersedes", "")])]


UNHELD_TYPE_IRI = "https://shop.example/kb/gadget/prices-are-reviewed-monthly"


@when(
    "the client creates a decision that supersedes an IRI under a type the store does not hold, saying which role and why",
    target_fixture="refused",
)
def _create_superseding_under_a_type_not_held(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "supersedes": UNHELD_TYPE_IRI, "sections": SECTIONS,
    }, message="Record it")


@given("a process type")
def _a_process_type(client):
    define(client, PROCESS_TYPE)


@when(
    "the client creates a decision that supersedes an IRI the store does not hold, under the process type, saying "
    "which role and why",
    target_fixture="refused",
)
def _create_superseding_under_the_process_type(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "supersedes": iri("process", "prices-are-reviewed-monthly"), "sections": SECTIONS,
    }, message="Record it")


@when(
    "the client creates a decision that is missing its purpose and supersedes an IRI under a type the store does not "
    "hold, saying which role and why",
    target_fixture="attempt",
)
def _create_with_two_faults_under_a_type_not_held(client, tmp_path):
    before = held.everything_in(tmp_path)
    response = request(client, "decision", "Price reviews happen weekly", {
        "supersedes": UNHELD_TYPE_IRI, "sections": [SECTIONS[1]],
    }, message="Record it")
    return {
        "response": response, "before": before, "after": held.everything_in(tmp_path),
        "faults": [("sections", "sections"), ("supersedes", "ref")],
    }


@when(
    "the client creates a decision whose options are of a shape the type does not allow and which is also missing its "
    "purpose, saying which role and why",
    target_fixture="attempt",
)
def _create_with_two_kinds_of_fault(root, client):
    before = held.holds(root)
    response = request(client, "decision", "Price reviews happen weekly", {"sections": SECTIONS[1:], "options": "Keep weekly"})
    return {
        "response": response, "before": before, "after": held.holds(root),
        "faults": [("options", "type"), ("sections", "sections")],
    }


WHOLE = "sections:\n  - title: Purpose\n    body: Why.\n  - title: Rationale\n    body: Because.\n"
SENSELESS = {
    "content that cannot be read as written at all": (WHOLE + "options: [Keep weekly\n", ""),
    "content holding text written with an escape for half of a character, which no text can hold":
        (WHOLE + 'options:\n  - title: "\\ud800"\n', "options/0/title"),
    "content holding an escape for the first half of a character, followed by text that is not its other half":
        (WHOLE + 'options:\n  - title: "Keep \\ud83d weekly"\n', "options/0/title"),
    "content holding an escape for the second half of a character, with no first half before it":
        (WHOLE + 'options:\n  - title: "Keep \\ude00 weekly"\n', "options/0/title"),
    "content that is a list rather than a set of named entries": ("- Purpose\n- Rationale\n", ""),
    "content that is a single bare value": ("Keep prices in step with costs.\n", ""),
    "content with nothing in it at all": ("", ""),
    "content whose sections are one line of text rather than sections":
        ("sections: Keep prices in step with costs.\n", "sections"),
    "content whose options are a single value rather than a collection": (WHOLE + "options: Keep weekly\n", "options"),
    "content one of whose options is a bare value": (WHOLE + "options:\n  - Keep weekly\n", "options/0"),
}


@when(
    parsers.re(f"the client creates a decision from (?P<senseless>{'|'.join(map(re.escape, SENSELESS))}), "
               "saying which role and why"),
    target_fixture="attempt",
)
def _create_from_senseless_content(root, client, senseless):
    before = held.holds(root)
    text, place = SENSELESS[senseless]
    response = _raw(client, text)
    return {"response": response, "before": before, "after": held.holds(root), "place": place}


REASONS = {
    "content cannot be read as written": ("content", "it is not YAML that can be read"),
    "content is a set of named entries": ("content", "content is a set of named entries"),
    "the content does not fit the type": ("type", ""),
}


@then(parsers.re(
    f"the artifact is rejected because (?P<reason>{'|'.join(map(re.escape, REASONS))}), "
    "and the place it went wrong is named"
))
def _rejected_for_senseless_content(attempt, reason):
    refused, (rule, words) = attempt["response"], REASONS[reason]
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.place, fault.rule) for fault in refused.faults] == [(attempt["place"], rule)]
    assert words in refused.faults[0].message


@then("the call comes back with its answer rather than breaking off")
def _the_call_answers(attempt):
    assert isinstance(attempt["response"].response, kb_pb2.CreateResponse)
    assert attempt["response"].faults


@when('the client creates a decision carrying a field written "2026-09-24", saying which role and why', target_fixture="created")
def _create_with_a_bare_date(client):
    text = content.dumps({"sections": SECTIONS}) + "options:\n  - title: Revisit\n    body: 2026-09-24\n"
    return request(client, "decision", "Review prices again", text, message="Say when to revisit")


@then("that field reads back as the text that was written, not as a date")
def _field_is_text_not_a_date(root, client, created):
    assert not created.faults, created.faults
    assert content.loads(read(client, created.id, whole=True).content)["options"][0]["body"] == "2026-09-24"
    on_disk = held.artifact(root, created.id)
    assert on_disk["options"][0]["body"] == "2026-09-24"


@when(
    "the client creates a decision whose rationale carries a title and an empty body, saying which role and why",
    target_fixture="created",
)
def _create_with_an_empty_rationale(client):
    return create(client, "decision", {
        "title": "Price reviews happen weekly",
        "sections": [SECTIONS[0], {"title": "Rationale", "body": ""}],
    }, message="Say why later")


@then("the rationale reads back with an empty body")
def _rationale_reads_back_empty(root, client, created):
    rationale = read(client, created.id, section="Rationale")
    assert not rationale.faults, rationale.faults
    assert content.loads(rationale.content) == {"title": "Rationale", "body": ""}
    on_disk = held.artifact(root, created.id)
    assert on_disk["sections"][1] == {"title": "Rationale", "body": ""}


@when(
    "the client creates a decision one of whose lines of prose ends in a space, saying which role and why",
    target_fixture="attempt",
)
def _create_with_a_line_ending_in_a_space(root, client):
    before = held.holds(root)
    text = (
        "sections:\n  - title: Purpose\n    body: |\n      Keep prices in step with costs.\n"
        "  - title: Rationale\n    body: |\n      Costs move weekly. \n      So we review weekly.\n"
    )
    response = _raw(client, text)
    return {"response": response, "before": before, "after": held.holds(root)}


@then(
    "the artifact is rejected because every piece of prose is written as a block, and this prose could not be "
    "written back as one, and the place that prose stands is named"
)
def _rejected_as_prose_that_is_no_block(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.artifact, fault.rule, fault.place) for fault in refused.faults] == [
        (iri("decision", "price-reviews-happen-weekly"), "content", "sections/1/body"),
    ]
    assert refused.faults[0].message.startswith(
        "every piece of prose is written as a block, and this prose could not be written back as one"
    )


@scenario(
    "hand-over-content.feature",
    "A character beyond the first 65,536 written as two escapes reads back as that one character",
)
def test_a_character_beyond_the_first_65536_written_as_two_escapes_reads_back_as_that_one_character():
    pass


BEYOND = "\U0001F600"  # one character beyond the first 65,536, which JSON writes as the escapes 😀


@when(
    "the client creates a decision carrying a field written as a character beyond the first 65,536 in two escapes, "
    "one for each half, saying which role and why",
    target_fixture="created",
)
def _create_with_two_escapes(client):
    return _raw(client, WHOLE + 'options:\n  - title: "Keep \\ud83d\\ude00 weekly"\n')


@then("the two halves read together as that one character")
def _halves_read_together(client, created):
    assert not created.faults, created.faults
    title = content.loads(read(client, created.id, whole=True).content)["options"][0]["title"]
    assert title == f"Keep {BEYOND} weekly"
    assert len(title) == len("Keep - weekly")


@then("the field reads back holding it")
def _field_reads_back_holding_it(root, client, created):
    assert content.loads(read(client, created.id, whole=True).content)["options"][0]["title"] == f"Keep {BEYOND} weekly"
    assert held.artifact(root, created.id)["options"][0]["title"] == f"Keep {BEYOND} weekly"


@scenario("hand-over-content.feature", "Content holding half of a character alone is refused")
def test_content_holding_half_of_a_character_alone_is_refused():
    pass


@then("the artifact is rejected because the content cannot be read as written")
def _rejected_as_unreadable_content(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert [(fault.place, fault.rule) for fault in refused.faults] == [(attempt["place"], "content")]
    assert "it is not YAML that can be read" in refused.faults[0].message


@given("the decision type declares its fields first, then its required sections, then its collection of options")
def _decision_type_in_reading_order(client):
    assert not next_version(client, "decision", ORDERED_DECISION_TYPE).faults


@when(
    "the client creates a decision written with its options first, then its sections, then its fields, where a "
    "field breaks two rules of the type, the second option is of a shape the type does not allow, and the "
    "rationale is missing, saying which role and why",
    target_fixture="attempt",
)
def _create_a_misordered_decision(root, client):
    before = held.everything_in(root)
    response = request(client, "decision", "Price reviews happen weekly", MISORDERED_DECISION, message="Record it")
    return {"response": response, "before": before, "after": held.everything_in(root)}


@then("the artifact is rejected with every fault, each naming the artifact, the place in it and the rule broken")
def _rejected_with_every_fault(attempt):
    refused = attempt["response"]
    assert (refused.id, refused.revision) == ("", 0)
    assert {fault.artifact for fault in refused.faults} == {iri("decision", "price-reviews-happen-weekly")}
    assert sorted((fault.place, fault.rule) for fault in refused.faults) == sorted(READING_ORDER)


@then(
    "the faults come in the order the places stand in the decision as it would read back: the field first, then "
    "the sections, then the options"
)
def _faults_in_reading_order(attempt):
    faults = [(fault.place, fault.rule) for fault in attempt["response"].faults]
    assert [place for place, _ in faults] == [place for place, _ in READING_ORDER]


@then("the two faults at the field come in the alphabetical order of the names of the rules they break")
def _two_faults_at_the_field_in_rule_order(attempt):
    assert [fault.rule for fault in attempt["response"].faults if fault.place == "status"] == ["maxLength", "pattern"]


# Slice 168: a placeholder is filled by creating what it names.

PARTS_DECISION_TYPE = copy.deepcopy(DECISION_TYPE)
PARTS_DECISION_TYPE["schema"]["properties"]["supersedes"]["ref"]["parts"] = True
ROLLBACK = f"{NOT_HELD}#options/rollback"
FIRST_DECISION = iri("decision", "price-reviews-happen-weekly")


def _listed(client):
    asked = placeholders(client)
    assert not asked.faults, asked.faults
    return [
        (each.id, [(link.artifact, link.field, link.place, link.part) for link in each.links])
        for each in asked.placeholders
    ]


@given(
    "a store holding a decision type whose artifacts require a purpose then a rationale, "
    "may link to the decision they supersede or into one of its options, and may carry a collection of options",
    target_fixture="client",
)
def _store_with_decision_type_linking_into_options(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, PARTS_DECISION_TYPE)
    return client


@when(
    "the client creates a decision that supersedes an option of a decision the store does not hold, at an IRI under "
    "the decision type, saying which role and why",
    target_fixture="created",
)
def _create_superseding_an_option_not_held(client):
    return request(client, "decision", "Price reviews happen weekly", {
        "supersedes": f"{NOT_HELD}#options/keep-weekly", "sections": SECTIONS,
    }, message="Record it")


@then("asked for the placeholders, the client is given the IRI the link points at, with the new decision linking to it")
def _the_placeholders_give_the_iri_with_the_part(client, created):
    assert _listed(client) == [(NOT_HELD, [(created.id, "supersedes", "supersedes", "options/keep-weekly")])]


@given(parsers.parse('a decision the store holds, with no option named "{name}"'))
def _a_decision_with_no_such_option(client, name):
    assert name not in {slug(option["title"]) for option in OPTIONS}
    held_one = request(client, "decision", "Prices are reviewed monthly", {"sections": SECTIONS, "options": OPTIONS})
    assert held_one.id == NOT_HELD, held_one.faults


@when(
    parsers.parse('the client creates a decision that supersedes the option "{name}" of that decision, saying which role and why'),
    target_fixture="refused",
)
def _create_superseding_an_option_not_there(client, name):
    return request(client, "decision", "Price reviews happen weekly", {
        "supersedes": f"{NOT_HELD}#options/{name}", "sections": SECTIONS,
    }, message="Record it")


@given("a decision that supersedes a decision the store does not hold, at an IRI under the decision type")
def _a_decision_waiting_on_a_decision(client):
    first = request(client, "decision", "Price reviews happen weekly", {"supersedes": NOT_HELD, "sections": SECTIONS})
    assert first.id == FIRST_DECISION, first.faults
    assert [each[0] for each in _listed(client)] == [NOT_HELD]


@when("the client creates a decision at that IRI, saying which role and why", target_fixture="created")
def _create_at_the_iri_waited_on(client):
    return request(client, "decision", "Prices are reviewed monthly", {"sections": SECTIONS}, message="Record it")


@then("following the link from the first decision reaches the new decision")
def _following_reaches_the_new_decision(client, created):
    assert created.id == NOT_HELD, created.faults
    reached = refs(client, FIRST_DECISION, 1)
    assert not reached.faults, reached.faults
    assert [each.stub.id for each in reached.reached] == [NOT_HELD]
    assert not check(client).violations


@then("asked for the placeholders, the client is not given that IRI")
def _the_placeholders_do_not_give_the_iri(client):
    assert NOT_HELD not in [each[0] for each in _listed(client)]


# This scenario's decision waited on is the one `_given_iri_and_first_version` names, the other links to it.
@given(
    parsers.parse(
        'a decision that supersedes the option "{name}" of a decision the store does not hold, at an IRI under the '
        "decision type"
    )
)
def _a_decision_waiting_on_an_option(client, name):
    first = request(client, "decision", "Prices are reviewed monthly", {
        "supersedes": f"{FIRST_DECISION}#options/{name}", "sections": SECTIONS,
    })
    assert first.id == NOT_HELD, first.faults
    assert [each[0] for each in _listed(client)] == [FIRST_DECISION]


@when(
    parsers.parse('the client creates a decision at that IRI with no option named "{name}", saying which role and why'),
    target_fixture="created",
)
def _create_at_the_iri_without_the_option(client, name):
    assert name not in {slug(option["title"]) for option in OPTIONS}
    return request(client, "decision", "Price reviews happen weekly", {
        "sections": SECTIONS, "options": OPTIONS,
    }, message="Record it")


@then("asked for the placeholders, the client is given the IRI the link points at, with the first decision linking to it")
def _the_placeholders_still_give_the_iri(client, created):
    assert created.id == FIRST_DECISION, created.faults
    assert _listed(client) == [(FIRST_DECISION, [(NOT_HELD, "supersedes", "supersedes", "options/rollback")])]


# Slice 170.1: a link that waits keeps waiting when its artifact changes. Here the first decision is the one that
# links, FIRST_DECISION, and the second the one linked to, at NOT_HELD.

@given(
    parsers.parse(
        'a decision that supersedes the option "{name}" of a second decision, the second created afterwards with no '
        'option named "{name_again}"'
    )
)
def _a_decision_waiting_on_an_option_its_target_was_created_without(client, name, name_again):
    assert name == name_again and name not in {slug(option["title"]) for option in OPTIONS}
    first = request(client, "decision", "Price reviews happen weekly", {
        "supersedes": f"{NOT_HELD}#options/{name}", "sections": SECTIONS,
    })
    assert first.id == FIRST_DECISION, first.faults
    second = request(client, "decision", "Prices are reviewed monthly", {"sections": SECTIONS, "options": OPTIONS})
    assert second.id == NOT_HELD, second.faults
    assert _listed(client) == [(NOT_HELD, [(FIRST_DECISION, "supersedes", "supersedes", f"options/{name}")])]


@when(
    "the client replaces the first decision's rationale, leaving what it supersedes as it is, saying which role and why",
    target_fixture="changed",
)
def _replace_the_rationale_of_the_decision_that_waits(client):
    return replace(
        client, FIRST_DECISION, {"title": "Rationale", "body": "Costs now move daily.\n"},
        message="Say why again", path="sections/rationale",
    )


@then("the change is accepted")
def _the_change_is_accepted(root, changed):
    assert not changed.faults, changed.faults
    assert changed.revision == 2
    assert held.artifact(root, FIRST_DECISION)["sections"][1]["body"] == "Costs now move daily.\n"
    assert held.artifact(root, FIRST_DECISION)["supersedes"] == ROLLBACK


@then("asked for the placeholders, the client is still given the IRI the link points at, with the first decision linking to it")
def _the_placeholders_still_give_the_part_waited_on(client):
    assert _listed(client) == [(NOT_HELD, [(FIRST_DECISION, "supersedes", "supersedes", "options/rollback")])]


def test_removing_the_artifact_that_filled_a_placeholder_is_refused_for_the_link_naming_the_linking_artifact(root):
    client = kb_client.connect(root)
    start_a_store(root)
    define(client, DECISION_TYPE)
    linking = request(client, "decision", "Price reviews happen weekly", {"supersedes": NOT_HELD, "sections": SECTIONS})
    assert not linking.faults, linking.faults
    filled = request(client, "decision", "Prices are reviewed monthly", {"sections": SECTIONS})
    assert filled.id == NOT_HELD, filled.faults
    refused = remove(client, NOT_HELD)
    assert [(fault.rule, fault.artifact) for fault in refused.faults] == [("on_delete", linking.id)], refused.faults
    assert not read(client, NOT_HELD).faults
