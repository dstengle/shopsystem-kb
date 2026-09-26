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

  @slice-82
  Scenario Outline: Asking by a kind the store holds no type for is refused
    Pins that an unknown kind is the same plain refusal wherever it is asked for, so a typo is never answered with an empty result that reads exactly like an empty store.
    Given a store that holds no type called "invoice"
    When the client <call>
    Then the call is rejected because a kind must name a type the store holds, and the kind asked for is given back

    Examples:
      | call                                                              |
      | lists the artifacts of the kind "invoice"                         |
      | searches the prose for restocking among artifacts of that kind    |
      | follows the links into a decision, only from artifacts of that kind |
