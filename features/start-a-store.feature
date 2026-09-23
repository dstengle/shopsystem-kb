Feature: Start a store
So that a client has somewhere to keep typed artifacts before it has any types of its own, the client can start a store.

  @slice-1
  Scenario: The client starts a store
    Given an empty directory
    When the client starts a store there
    Then the store holds the one type that describes what a type is
    And the store holds no other type and no content
    And the client can define its own types straight away
