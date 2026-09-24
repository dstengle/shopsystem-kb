Feature: Look after a store
So that a store exists and can be checked from a shell without any client, the operator can look after a store.

  @slice-44
  Scenario: The operator sets up a store
    Given a directory that has no store inside it
    When the operator runs kb init against that directory, saying which role they are
    Then there is a store inside that directory, in a place of its own
    And a client can begin defining its own types in it straight away

  @slice-44
  Scenario: Setting up a store without naming which role is refused
    Given a directory that has no store inside it, and nothing names which role the operator is
    When the operator runs kb init against that directory
    Then setting the store up is rejected because the role must be named through KB_ACTOR
    And that directory still has no store inside it

  @slice-44
  Scenario: Setting up a store where the directory already has one inside it is refused
    Given a directory that already has a store inside it, with content in that store
    When the operator runs kb init against that directory, saying which role they are
    Then setting the store up is rejected because that directory already has a store inside it
    And the store that is there holds what it held before

  @slice-44
  Scenario: Setting up a store inside a store is refused
    Given a directory that sits inside a store
    When the operator runs kb init against that directory, saying which role they are
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

  @slice-54
  Scenario: The operator reads an artifact's file on disk
    Given a store holding a decision whose purpose is one short line and which carries a list of options
    When the operator opens the decision's file
    Then every piece of prose stands as a block of its own, however short it is
    And each list is written beneath the name it belongs to, indented under it
    And no line of prose has been broken to fit a width
    And nothing in the file tells a reader how to build a value

  @slice-62
  Scenario: The same content always lands on disk as the same bytes
    Given two stores each given the same decision by the same client
    When the operator compares the two decision files
    Then the two files are the same, byte for byte

  @slice-44
  Scenario: The operator checks the store from a folder inside it
    Given a store, with the operator working in a folder deep inside the directory it sits in
    When the operator runs kb validate there
    Then the store found above where they are working is the one checked

  @slice-44
  Scenario: The operator names the store instead of standing in it
    Given a store, with the operator working outside any store and KB_ROOT naming that one
    When the operator runs kb validate there
    Then the store KB_ROOT names is the one checked

  @slice-44
  Scenario: Running the command line where no store can be found is refused
    Given the operator is working outside any store and nothing names one
    When the operator runs kb validate there
    Then the check is rejected because no store was found, neither above where they are working nor named outright

  @slice-44
  Scenario: Naming a store that is not there is refused
    Given the operator is working outside any store, with KB_ROOT naming a directory that holds no store
    When the operator runs kb validate there
    Then the check is rejected because KB_ROOT names a directory that holds no store

  @slice-44
  Scenario: Standing in one store while naming another is refused
    Given the operator is working inside a store, with KB_ROOT naming a different store
    When the operator runs kb validate there
    Then the check is rejected because KB_ROOT names a store other than the one they are standing in, and neither of the two is guessed at
