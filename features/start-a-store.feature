Feature: Start a store
So that a client has somewhere to keep typed artifacts before it has any types of its own, the client can start a store.

  @slice-1
  Scenario: The client starts a store
    Given an empty directory
    When the client starts a store there
    Then the store holds the one type that describes what a type is
    And the store holds no other type and no content
    And the client can define its own types straight away

  Scenario: A directory holding other things can still be given a store
    Given a directory holding files that have nothing to do with a store
    When the client starts a store there
    Then the store is made inside that directory, in a place of its own
    And the files that were already there are left as they were, and none of them is the store's concern

  Scenario: Starting a store in a directory that already has one inside it is refused
    Given a directory that already has a store inside it, with content in that store
    When the client starts a store there
    Then starting the store is rejected because that directory already has a store inside it
    And the store that is there holds what it held before

  Scenario: Starting a store inside a store is refused
    Given a directory that sits inside a store
    When the client starts a store there
    Then starting the store is rejected because that directory is inside a store
    And the store it sits inside holds what it held before
