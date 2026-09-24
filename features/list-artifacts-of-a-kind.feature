Feature: List artifacts of a kind
So that a client can show everything of one kind without knowing any names, the client can list artifacts of a kind.

  Background:
    Given a store holding three decisions, one of them superseded

  @slice-29
  Scenario: The client lists every artifact of a kind
    Pins the way into the store when a client knows no names at all: ask by kind and get a stub of each one.
    When the client lists the decisions
    Then the client is given a stub of each of the three

  @slice-29
  Scenario: The client lists the artifacts matching a field
    Pins that a listing can be narrowed by a field, so the common "show me only these" question is answered by the store rather than by the client sifting.
    When the client lists the decisions that are superseded
    Then the client is given only the superseded one

  @slice-29
  Scenario: The client lists names only
    Pins that a client can ask for just the names, for when it means to work through them one by one and does not want everything up front.
    When the client lists the decisions asking for names only
    Then the client is given three names and nothing else
