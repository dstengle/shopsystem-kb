Feature: Remove an artifact
So that a client can take out what is no longer used without leaving links pointing at nothing, the client can remove an artifact.

  Background:
    Given a store holding a tag nothing points at
    And a tag a decision points at
    And a process one of whose steps a work item points at

  @assumes-every-change-is-recorded
  Scenario: The client removes an artifact nothing points at
    When the client removes the tag nothing points at, saying which role and why
    Then the store no longer holds it
    And the removal is recorded like any other change

  @assumes-refusing-is-the-only-answer-to-a-blocked-removal
  Scenario: A removal something points at is refused
    When the client removes the tag the decision points at, saying which role and why
    Then the removal is rejected because something still points at it
    And the client is given every link that blocks it

  @assumes-refusing-is-the-only-answer-to-a-blocked-removal
  Scenario: A removal is refused for a link into something inside the artifact
    When the client removes the process, saying which role and why
    Then the removal is rejected because something still points at a node beneath it
