# formulated from spec/capabilities/check-the-store.md
Feature: Check the store
  Narrator: the client

  @slice-43
  Scenario: A store with nothing wrong reports nothing
    Pins the quiet case: a healthy store says so plainly, so silence is a real answer rather than a check that did not run.
    Given a store where everything fits its type
    When the client checks the store
    Then the client is told of no violation

  @slice-43
  Scenario: Every violation is reported
    Pins that a check sweeps the whole store and reports every fault it finds, each placed precisely, rather than stopping at the first.
    Given a store where one artifact is missing a section its type requires and another points at something the store does not hold
    When the client checks the store
    Then both are reported, each naming the artifact, the place in it and the rule broken

  @slice-43
  Scenario: An artifact behind its type is reported as stale
    Pins that falling behind a type is news, not damage: it is listed on its own so nobody has to fix it before the store can be trusted.
    Given a store where a decision was last checked against an older version of the decision type
    When the client checks the store
    Then that decision is listed as behind its type
    And it is not reported as a violation

  @slice-43
  Scenario: An artifact behind its type that no longer fits it is reported both ways
    Pins that being behind and being wrong are separate findings, and that the check still comes back with an answer when both are true of one artifact.
    Given a store where a decision was last checked against an older version of the decision type, and no longer fits the current version
    When the client checks the store
    Then that decision is listed as behind its type
    And it is also reported as a violation, naming the artifact, the place in it and the rule broken
    And the check itself does not fail
