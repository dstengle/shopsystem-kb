# formulated from spec/capabilities/make-several-changes-in-one-go.md
Feature: Make several changes in one go
  Narrator: the client

  Background:
    Given a store holding a decision type and a work item

  @slice-5
  Scenario: The client makes several changes in one go
    Pins that a set of changes is one act: the store names the set itself, each change still reports its own result, and the history shows one change rather than several.
    When the client asks, in one go, for a decision to be created and the work item to point at it, in that order, saying which role and why
    Then the client is given one name for the set, which the client never asked for
    And each change also comes back with its own result
    And the store's history shows the set as one change

  @slice-51
  Scenario: The name given for a set finds the set in the history
    Pins that the name handed back is the one the history uses, so a client can go from having made a set to seeing exactly what it did.
    When the client asks, in one go, for a decision to be created and the work item to point at it, in that order, saying which role and why
    Then the changes the history shows under the name the client was given for the set are exactly those two

  @slice-6
  Scenario: One bad change in a set leaves the store untouched
    Pins that a set is all or nothing, and that the refusal still accounts for every fault so the whole set can be fixed in one more attempt.
    Given a set whose second change is missing a section its type requires
    When the client asks for the set, saying which role and why
    Then the set is rejected because a change in it does not fit its type
    And the store holds neither change
    And every fault in the set comes back, not only the first

  @slice-85
  Scenario Outline: A set stopped for any reason at all leaves the store exactly as it was
    Pins all-or-nothing for every way a set can be stopped, not only a change that does not fit: the whole set is worked out and checked before anything is written, so nothing ever half-lands.
    When the client asks, in one go, for a set in which <fault>, saying which role and why
    Then the set is rejected because <reason>
    And the store holds none of the changes in the set
    And the store's history holds no entry for any of them

    Examples:
      | fault                                                                | reason                                                                  |
      | the second change names an artifact the store holds nothing under    | the store holds nothing by that name, and the name asked for is given back |
      | the second change removes an artifact something still points at      | something still points at it                                            |

  @slice-97
  Scenario: A set holding no changes at all is refused
    Pins that a set is a request to change something, so asking for nothing is a mistake the client is told about rather than a change the store records, and the store is left exactly as it was.
    When the client asks, in one go, for a set holding no changes at all, saying which role and why
    Then the set is rejected because a set must hold at least one change
    And the store holds no artifact it did not hold before
    And the store's history holds no entry for it

  @slice-70
  Scenario: Two changes to one artifact in one set each leave their own entry
    Pins that a set is still a set of changes: each one counts the artifact's version up and is recorded on its own, even though the set as a whole lands once.
    When the client asks, in one go, for the work item to be changed twice, saying which role and why
    Then the store's history holds an entry for each of the two changes
    And each entry records the version that change left behind
    And the work item's version has gone up by two

  @slice-107
  Scenario Outline: A change in a set points at what another change in it makes, earlier or later
    Pins the two clocks a set runs on: a link may point at what any change in the set makes, before or after it, because links are judged against the set's end, while each change itself acts only on what the changes before it have done.
    When the client asks, in one go, for <changes>, in that order, saying which role and why
    Then <outcome>

    Examples:
      | changes                                                              | outcome                                                                                                |
      | a decision to be created and the work item to point at it            | the set lands, and the work item points at the new decision                                            |
      | the work item to point at a decision and that decision to be created | the set lands, and the work item points at the new decision                                            |
      | a decision to be created and that decision to be replaced            | the set lands, and the decision holds the replacement                                                  |
      | a decision to be replaced and that decision to be created            | the set is rejected because the store holds nothing by that name, and the name asked for is given back |

  @slice-107
  Scenario: Two new artifacts in one set that point at each other land
    Pins that a set is checked as a whole, so two artifacts that each need the other to exist can be made together, which no order of single changes allows.
    Given the decision type lets a decision point at another decision
    When the client asks, in one go, for two decisions to be created, each pointing at the other, saying which role and why
    Then the set lands
    And the store holds both decisions, each pointing at the other

  @slice-115
  Scenario: A set that waits longer than the store waits for another change is refused as busy
    Pins that a set is held to the same wait as a single change: refused as busy, none of it written, and free to be asked for again.
    Given another change is being written and holds the store longer than the store waits
    When the client asks, in one go, for a decision to be created and the work item to point at it, in that order, saying which role and why
    Then the set is rejected because the store was busy with another change
    And nothing is written
    And the same set may be asked for again
