Feature: List artifacts of a kind
So that a client can show everything of one kind without knowing any names, the client can list artifacts of a kind.

  Background:
    Given a store holding three decisions, one of them superseded

  @assumes-typed-refs-cover-the-questions
  Scenario: The client lists every artifact of a kind
    When the client lists the decisions
    Then the client is given a stub of each of the three

  @assumes-typed-refs-cover-the-questions
  Scenario: The client lists the artifacts matching a field
    When the client lists the decisions that are superseded
    Then the client is given only the superseded one

  @assumes-typed-refs-cover-the-questions
  Scenario: The client lists names only
    When the client lists the decisions asking for names only
    Then the client is given three names and nothing else
