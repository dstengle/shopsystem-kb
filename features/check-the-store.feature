Feature: Check the store
So that a client can tell whether everything the store holds still fits its type, the client can check the store.

  @assumes-the-contract-is-the-only-way-in
  Scenario: A store with nothing wrong reports nothing
    Given a store where everything fits its type
    When the client checks the store
    Then the client is told of no violation

  @assumes-all-faults-come-back-not-the-first
  Scenario: Every violation is reported
    Given a store where one artifact is missing a section its type requires and another points at something the store does not hold
    When the client checks the store
    Then both are reported, each naming the artifact, the place in it and the rule broken

  @assumes-being-behind-a-type-is-not-a-fault
  Scenario: An artifact behind its type is reported as stale
    Given a store where a decision was last checked against an older version of the decision type
    When the client checks the store
    Then that decision is listed as behind its type
    And it is not reported as a violation
