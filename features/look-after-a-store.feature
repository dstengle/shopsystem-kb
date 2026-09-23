Feature: Look after a store
So that a store exists and can be checked from a shell without any client, the operator can look after a store.

  @slice-44
  Scenario: The operator sets up a store
    Given a directory that holds no store
    When the operator runs kb init against that directory
    Then there is a store at that path
    And a client can begin defining its own types in it straight away

  Scenario: Setting up a store where there is one already is refused
    Given a directory that already holds a store with content in it
    When the operator runs kb init against that directory
    Then setting the store up is rejected because the root already holds a store
    And the store that is there holds what it held before

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
