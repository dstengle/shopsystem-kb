# formulated from spec/capabilities/serve-a-store-for-tests.md
Feature: Serve a store for tests
  Narrator: the client

  Background:
    Given a store the client started, holding a decision
    And a directory other than the one the store sits in

  Scenario: The client serves a started store for its tests, naming another directory to hold the connection
    Pins that a client's own tests can put a store behind kb's own server and reach it the way a served store is reached, without anyone running kb serve.
    When the client serves the store for its tests, naming that other directory to hold the connection
    Then the client is given the address the store is served at
    And a client working in that other directory reads the decision through a server at that address

  Scenario Outline: The client's tests are done with a store they served, however they ended
    Pins that serving a store for tests leaves nothing behind: whatever became of the tests, no server is left running and no connection is left pointing at one.
    Given the client is serving the store for its tests, naming that other directory to hold the connection
    When the client's tests are done with the store, having <ended>
    Then the server at the address the client was given no longer answers
    And that other directory no longer holds the connection

    Examples:
      | ended                    |
      | passed                   |
      | broken off with an error |

  Scenario: The client serves a store for its tests with a clock
    Pins that a client's tests can say when the changes made through the server they serve happen, so they can lay down a history across several days through a served store without waiting for them.
    Given the client is serving the store for its tests with a clock that reads 2026-09-23 at 14:30, naming that other directory to hold the connection
    And a client working in that other directory, readied with no clock of its own
    When that client creates a second decision
    Then every entry that change left in the journal says it happened at 2026-09-23 at 14:30
