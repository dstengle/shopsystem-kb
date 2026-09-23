Feature: Change an artifact
So that a client can keep an artifact true without rewriting the store, the client can change an artifact.

  Background:
    Given a store holding a decision with a purpose and a rationale, at its first version

  @assumes-every-change-is-recorded
  Scenario: The client changes an artifact
    When the client replaces the decision, saying which role and why
    Then the version goes up by one
    And the artifact records the current version of its type

  @assumes-parts-are-nodes-not-quoted-text
  Scenario: The client changes one node inside an artifact
    When the client replaces the rationale of the decision, saying which role and why
    Then only that section changes
    And the rest of the decision reads as before

  @assumes-every-change-is-validated-before-it-is-written
  Scenario: A change that would break the type leaves the artifact as it was
    When the client replaces the decision with content that has no purpose, saying which role and why
    Then the change is rejected because the sections the type requires must all be present, in order
    And reading the decision gives what it held before, at the version it held before
