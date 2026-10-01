# formulated from spec/capabilities/find-the-store.md
Feature: Find the store
  Narrator: the client

  Background:
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items

  @slice-1.3
  Scenario: The client works in a folder inside the store
    Pins that a client finds its store by looking upward from where it is working, the way git finds a repository.
    Given the client is working in a folder deep inside the directory the store sits in
    When the client reads the decision
    Then the client is given the decision, from the store found above where it is working

  @slice-1.8
  Scenario: The client names the store instead of working inside it
    Pins the other way of saying which store is meant, for a client that runs from outside one.
    Given the client is working outside any store, with KB_ROOT naming this one
    When the client reads the decision
    Then the client is given the decision, from the store KB_ROOT names

  @slice-1.8
  Scenario: A call with no store to be found is refused
    Pins that finding no store is a refusal the client can handle, not an exception thrown out of a call.
    Given the client is working outside any store and nothing names one
    When the client reads the decision
    Then the read is rejected because no store was found, neither above where it is working nor named outright

  @slice-1.8
  Scenario: Naming a store that is not there is refused
    Pins that naming a store that is not there is its own refusal, rather than a silent fall back to looking upward.
    Given the client is working outside any store, with KB_ROOT naming a directory that holds no store
    When the client reads the decision
    Then the read is rejected because KB_ROOT names a directory that holds no store
    And no content comes back

  @slice-1.8
  Scenario: Working in one store while naming another is refused
    Pins that two candidate stores is a refusal and never a preference, so a read never quietly comes from somewhere the client did not expect.
    Given the client is working inside a store, with KB_ROOT naming a different store
    When the client reads the decision
    Then the read is rejected because KB_ROOT names a store other than the one it is working in, and neither of the two is guessed at
    And no content comes back, from either store

  @slice-99
  Scenario Outline: The client names the store from a working directory that has since been removed
    Pins that losing the working directory takes away only the looking upward: KB_ROOT still reaches its store, and a directory that is gone is inside no store, so it cannot disagree with the one KB_ROOT names.
    Given the client is working in <where>, which has since been removed, with KB_ROOT naming this store
    When the client reads the decision
    Then the client is given the decision, from the store KB_ROOT names

    Examples:
      | where                                                        |
      | a directory outside any store                                |
      | a folder deep inside the directory a different store sits in |

  @slice-99
  Scenario Outline: A call from a working directory that has since been removed, with nothing naming a store, is refused
    Pins that a working directory that is gone is inside no store, so the store that once sat above it is not looked for or fallen back on, and the refusal says why rather than just that no store was found.
    Given the client is working in <where>, which has since been removed, and nothing names a store
    When the client reads the decision
    Then the read is rejected because the directory it is working in is gone
    And no content comes back

    Examples:
      | where                                                |
      | a directory outside any store                        |
      | a folder deep inside the directory the store sits in |

  @slice-99
  Scenario: A working directory that has gone is a fault the client is given, never an exception
    Pins that losing the place the client was working in ends the way every other failure to find a store does: an answer the client can handle, the call never breaking off.
    Given the client is working in a directory that has since been removed, and nothing names a store
    When the client reads the decision
    Then the client is given that refusal as it is given any other fault, the call never breaking off

  @slice-1.15
  Scenario: A client readied before there was a store finds the store started since
    Pins that a client binds to no store when it is made and works out where it is on every call, so long-lived clients and fresh stores do not need ordering.
    Given the client was readied to call a store while working where there was none and nothing named one
    And a store holding the decision has since been started where the client is working
    When the client reads the decision
    Then the client is given the decision
    And the client was never readied again after the store appeared

  @slice-88
  Scenario Outline: A KB_ROOT that names no store is refused, naming KB_ROOT
    Pins that naming the store outright is either right or refused: nothing about KB_ROOT is guessed at, and where the client happens to be working is never quietly fallen back on.
    Given the client is working outside any store, with KB_ROOT <state>
    When the client reads the decision
    Then the read is rejected because KB_ROOT names no store, and KB_ROOT is named back
    And where the client is working is not fallen back on
    And no content comes back

    Examples:
      | state                                    |
      | set to nothing at all                    |
      | naming a directory that is not there     |
      | naming a file rather than a directory    |
