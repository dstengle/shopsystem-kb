Feature: Change an artifact
So that a client can keep an artifact true without rewriting the store, the client can change an artifact.

  Background:
    Given a store holding a decision with a purpose and a rationale, at its first version

  @slice-22
  Scenario: The client changes an artifact
    When the client replaces the decision, saying which role and why
    Then the version goes up by one
    And the artifact records the current version of its type

  @slice-13
  Scenario: The client changes one node inside an artifact
    When the client replaces the rationale of the decision, saying which role and why
    Then only that section changes
    And the rest of the decision reads as before

  Scenario: Changing an artifact that is behind its type brings it up to date
    Given a decision last checked against an older version of the decision type, which still fits the current version
    When the client replaces the decision with content that fits the current version of its type, saying which role and why
    Then the decision records the current version of its type
    And it is no longer listed as behind its type

  @slice-8
  Scenario: A change that would break the type leaves the artifact as it was
    When the client replaces the decision with content that has no purpose, saying which role and why
    Then the change is rejected because the sections the type requires must all be present, in order
    And reading the decision gives what it held before, at the version it held before
