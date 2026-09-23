Feature: Look after a store
So that a store exists and can be checked from a shell without any client, the operator can look after a store.

  @slice-44
  Scenario: The operator sets up a store
    Given a directory that has no store inside it
    When the operator runs kb init against that directory
    Then there is a store inside that directory, in a place of its own
    And a client can begin defining its own types in it straight away

  @slice-44
  Scenario: Setting up a store where the directory already has one inside it is refused
    Given a directory that already has a store inside it, with content in that store
    When the operator runs kb init against that directory
    Then setting the store up is rejected because that directory already has a store inside it
    And the store that is there holds what it held before

  @slice-44
  Scenario: Setting up a store inside a store is refused
    Given a directory that sits inside a store
    When the operator runs kb init against that directory
    Then setting the store up is rejected because that directory is inside a store
    And the store it sits inside holds what it held before

  @slice-44
  Scenario: The operator checks the whole store
    Given a store whose content the operator did not write
    When the operator runs kb validate in that store
    Then the operator is told of everything in the store that does not fit its type, and where
    And of everything that is behind the type it was last checked against

  @slice-44
  Scenario: The command line does nothing to content
    Given a store
    When the operator asks what the command line offers
    Then it offers setting a store up and checking one
    And nothing that changes what the store holds
