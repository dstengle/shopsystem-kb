Feature: Read the journal
So that a client can show how the store came to hold what it holds, the client can read the journal.

  Background:
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today

  @slice-9
  Scenario: Every change leaves an entry
    When the client reads the journal for that decision
    Then there is one entry for each change
    And each entry says when it happened, which role made it, for which piece of work, what it did, to which artifact and place in it, the version it left behind, a fingerprint of what was written, and the message given

  @slice-34
  Scenario: The client reads the journal for one role
    When the client reads the journal for the shopkeeper
    Then the client is given only the creation of the decision

  @slice-34
  Scenario: The client reads the journal for one piece of work
    When the client reads the journal for that piece of work
    Then the client is given only the change the agent made

  @slice-34
  Scenario: The client reads the journal since a time
    When the client reads the journal since 2026-09-22
    Then the client is given only the change made today
