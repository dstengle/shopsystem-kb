Feature: Check the store
So that a client can tell whether everything the store holds still fits its type, the client can check the store.

  @slice-42
  Scenario: A store with nothing wrong reports nothing
    Given a store where everything fits its type
    When the client checks the store
    Then the client is told of no violation

  @slice-10
  Scenario: Every violation is reported
    Given a store where one artifact is missing a section its type requires and another points at something the store does not hold
    When the client checks the store
    Then both are reported, each naming the artifact, the place in it and the rule broken

  @slice-42
  Scenario: An artifact behind its type is reported as stale
    Given a store where a decision was last checked against an older version of the decision type
    When the client checks the store
    Then that decision is listed as behind its type
    And it is not reported as a violation

  Scenario: An artifact behind its type that no longer fits it is reported both ways
    Given a store where a decision was last checked against an older version of the decision type, and no longer fits the current version
    When the client checks the store
    Then that decision is listed as behind its type
    And it is also reported as a violation, naming the artifact, the place in it and the rule broken
    And the check itself does not fail
