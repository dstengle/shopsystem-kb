Feature: Make several changes in one go
So that a set of changes that only makes sense together is never half-applied, the client can make several changes in one go.

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
      | the second change touches an artifact whose stored file cannot be read | that file cannot be read, and the file is named                        |

  Scenario: Two changes to one artifact in one set each leave their own entry
    Pins that a set is still a set of changes: each one counts the artifact's version up and is recorded on its own, even though the set as a whole lands once.
    When the client asks, in one go, for the work item to be changed twice, saying which role and why
    Then the store's history holds an entry for each of the two changes
    And each entry records the version that change left behind
    And the work item's version has gone up by two
