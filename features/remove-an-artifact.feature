Feature: Remove an artifact
So that a client can take out what is no longer used without leaving links pointing at nothing, the client can remove an artifact.

  Background:
    Given a store holding a tag nothing points at
    And a tag a decision points at

  @slice-40
  Scenario: The client removes an artifact nothing points at
    When the client removes the tag nothing points at, saying which role and why
    Then the store no longer holds it
    And the removal is recorded like any other change

  @slice-40
  Scenario: A removal something points at is refused
    When the client removes the tag the decision points at, saying which role and why
    Then the removal is rejected because something still points at it
    And the client is given every link that blocks it

  Scenario: Removing something the store does not hold is refused
    When the client removes an artifact by a name the store holds nothing under, saying which role and why
    Then the removal is rejected because the store holds nothing by that name, and the name asked for is given back
    And the store holds what it held before
