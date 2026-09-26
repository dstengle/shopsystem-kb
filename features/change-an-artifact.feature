Feature: Change an artifact
So that a client can keep an artifact true without rewriting the store, the client can change an artifact.

  Background:
    Given a store holding a decision with a purpose and a rationale, at its first version

  @slice-23
  Scenario: The client changes an artifact
    Pins what a successful write leaves behind: the version counts up by one and the artifact records which version of its type it was checked against.
    When the client replaces the decision, saying which role and why
    Then the version goes up by one
    And the artifact records the current version of its type

  @slice-13
  Scenario: The client changes one node inside an artifact
    Pins that a change can be aimed at a node inside an artifact, so a client can correct one section without resending everything around it.
    When the client replaces the rationale of the decision, saying which role and why
    Then only that section changes
    And the rest of the decision reads as before

  @slice-23
  Scenario: Changing an artifact that is behind its type brings it up to date
    Pins that being behind the type is not a state to migrate out of separately: a write that fits the current version clears it as a side effect.
    Given a decision last checked against an older version of the decision type, which still fits the current version
    When the client replaces the decision with content that fits the current version of its type, saying which role and why
    Then the decision records the current version of its type
    And it is no longer listed as behind its type

  @slice-23
  Scenario: Changing an artifact that is behind its type with content the current version will not have is refused
    Pins that being behind buys no leniency: the write is checked against the current version like any other, and a failing one changes nothing, staleness included.
    Given a decision last checked against an older version of the decision type
    When the client replaces the decision with content that does not fit the current version of its type, saying which role and why
    Then the change is rejected because the content does not fit the current version of its type, like any change that does not fit
    And reading the decision gives what it held before, at the version it held before
    And it is still listed as behind its type

  @slice-8
  Scenario: A change that would break the type leaves the artifact as it was
    Pins check-then-swap: a change is applied to a copy and only lands if it passes, so a refused change is never visible afterwards.
    When the client replaces the decision with content that has no purpose, saying which role and why
    Then the change is rejected because the sections the type requires must all be present, in order
    And reading the decision gives what it held before, at the version it held before

  @slice-23
  Scenario: A change whose content settles what only the store settles is refused
    Pins that identity stays the store's business on a change as much as on a create: content cannot set its own version, and the offending entry is named back.
    When the client replaces the decision with content carrying a version of its own, saying which role and why
    Then the change is rejected because content holds only what the type declares, and the thing it carried that only the store settles is named back
    And reading the decision gives what it held before, at the version it held before

  @slice-23
  Scenario: Changing something the store does not hold is refused
    Pins that writing to an unknown name is an answer, not an accident: it names what was asked for and creates nothing.
    When the client replaces an artifact by a name the store holds nothing under, saying which role and why
    Then the change is rejected because the store holds nothing by that name, and the name asked for is given back
    And nothing is written anywhere in the store

  @slice-23
  Scenario: A change aimed at a name that is not a plain name writes nothing
    Pins that a name is checked for shape before any file is worked out from it, so a name dressed up as a path can never reach the disk, inside the store or out.
    When the client replaces an artifact named "../../elsewhere", saying which role and why
    Then the change is rejected because a name is a kind and a plain name of lower-case letters, digits and single hyphens
    And nothing is written anywhere, inside the store or outside it

  Scenario Outline: Every way the place a change is aimed at can be wrong is refused
    Pins that the place inside an artifact is checked before anything is touched, so a change that names nothing real is a plain refusal and the artifact is left exactly as it was.
    When the client <call>, saying which role and why
    Then the change is rejected because <reason>
    And reading the decision gives what it held before, at the version it held before

    Examples:
      | call                                                                       | reason                                                           |
      | replaces a place inside the decision the decision holds nothing under      | the decision holds nothing at that place                         |
      | replaces a place inside the decision that runs on past a piece of prose    | the decision holds nothing at that place                         |
      | replaces a place inside the decision beginning at the decision's own version | a place inside an artifact never names what only the store settles |
      | adds an item at a place inside the decision that is not a collection       | an item is added to a collection, and that place is not one      |

  Scenario: The client changes one item of a collection
    Pins that a change can be aimed at one item of a collection, and that the item keeps the name it was given, because a name is worked out once and never again.
    Given the decision carries two options
    When the client replaces one of the options, saying which role and why
    Then only that option changes
    And it keeps the name it was given when it was created
    And anything pointing at it still lands on it

  Scenario: Items sent back with their names are the same items, and one without a name is new
    Pins what a client sends when it rewrites a whole collection: the names the store gave are what say which item is which, and an item arriving without one is new and is named by the store.
    Given the decision carries two options
    When the client replaces the decision, sending both options back with the names they were given and a third option with no name, saying which role and why
    Then the two options are the same items as before, keeping their names
    And the third option is new and is given a name of its own

  Scenario Outline: Every way an item's name can be wrong on a change is refused
    Pins that item names are the store's to give and the client's only to hand back: anything else is refused rather than stored as the client wrote it.
    Given the decision carries two options
    When the client replaces the decision with options <items>, saying which role and why
    Then the change is rejected because <reason>
    And reading the decision gives what it held before, at the version it held before

    Examples:
      | items                                                        | reason                                                                    |
      | one of which carries a name no option of that decision has   | a name on an item names an item already in that collection                |
      | both of which carry the same name                            | the items of a collection each have a name of their own                   |
      | one of which carries a name that is not a plain name         | a name is a plain name of lower-case letters, digits and single hyphens   |
