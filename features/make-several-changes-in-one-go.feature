Feature: Make several changes in one go
So that a set of changes that only makes sense together is never half-applied, the client can make several changes in one go.

  Background:
    Given a store holding a decision type and a work item

  @assumes-batch-keeps-throughput-adequate
  Scenario: The client makes several changes in one go
    When the client asks, in one go, for a decision to be created and the work item to point at it, in that order, saying which role and why
    Then each change comes back with its own result
    And the store's history shows the set as one change

  @assumes-a-refused-write-changes-nothing
  Scenario: One bad change in a set leaves the store untouched
    Given a set whose second change is missing a section its type requires
    When the client asks for the set, saying which role and why
    Then the set is rejected because a change in it does not fit its type
    And the store holds neither change
    And every fault in the set comes back, not only the first
