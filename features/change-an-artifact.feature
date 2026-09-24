Feature: Change an artifact
So that a client can keep an artifact true without rewriting the store, the client can change an artifact.

  Background:
    Given a store holding a decision with a purpose and a rationale, at its first version

  @slice-22
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

  @slice-22
  Scenario: Changing an artifact that is behind its type brings it up to date
    Pins that being behind the type is not a state to migrate out of separately: a write that fits the current version clears it as a side effect.
    Given a decision last checked against an older version of the decision type, which still fits the current version
    When the client replaces the decision with content that fits the current version of its type, saying which role and why
    Then the decision records the current version of its type
    And it is no longer listed as behind its type

  @slice-22
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

  @slice-22
  Scenario: A change whose content settles what only the store settles is refused
    Pins that identity stays the store's business on a change as much as on a create: content cannot set its own version, and the offending entry is named back.
    When the client replaces the decision with content carrying a version of its own, saying which role and why
    Then the change is rejected because content holds only what the type declares, and the thing it carried that only the store settles is named back
    And reading the decision gives what it held before, at the version it held before

  @slice-22
  Scenario: Changing something the store does not hold is refused
    Pins that writing to an unknown name is an answer, not an accident: it names what was asked for and creates nothing.
    When the client replaces an artifact by a name the store holds nothing under, saying which role and why
    Then the change is rejected because the store holds nothing by that name, and the name asked for is given back
    And nothing is written anywhere in the store

  @slice-22
  Scenario: A change aimed at a name that is not a plain name writes nothing
    Pins that a name is checked for shape before any file is worked out from it, so a name dressed up as a path can never reach the disk, inside the store or out.
    When the client replaces an artifact named "../../elsewhere", saying which role and why
    Then the change is rejected because a name is a kind and a plain name of lower-case letters, digits and single hyphens
    And nothing is written anywhere, inside the store or outside it
