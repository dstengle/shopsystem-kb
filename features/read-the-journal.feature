Feature: Read the journal
So that a client can show how the store came to hold what it holds, the client can read the journal.

  Background:
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today

  @slice-9
  Scenario: Every change leaves an entry
    Pins that nothing changes the store unrecorded, and pins exactly what each record carries, since that is the whole of what can ever be asked about the past.
    When the client reads the journal for that decision
    Then there is one entry for each change
    And each entry says when it happened, which role made it, for which piece of work, what it did, to which artifact and place in it, the version it left behind, a fingerprint of what was written, the message given, and which set of changes it landed with

  @slice-35
  Scenario: The journal alone shows what landed together
    Pins that the journal is self-sufficient about grouping: what landed together is visible in the entries themselves, with a lone change its own set, so nothing outside has to be consulted.
    Given a store where two artifacts were changed in one go and a third was changed on its own
    When the client reads the journal
    Then the two entries from the one go name the same set of changes
    And the entry for the change made on its own names itself as its own set
    And the client can tell what landed together from the journal without reading anything else

  @slice-35
  Scenario: The client reads the journal for one role
    Pins the "who did this" question, answered by the journal rather than by the client reading everything.
    When the client reads the journal for the shopkeeper
    Then the client is given only the creation of the decision

  @slice-35
  Scenario: The client reads the journal for one piece of work
    Pins the "what did this piece of work change" question, which is how a run of work is accounted for after the fact.
    When the client reads the journal for that piece of work
    Then the client is given only the change the agent made

  @slice-35
  Scenario: The client reads the journal since a time
    Pins the "what has happened lately" question, so a client can catch up without walking the whole history.
    When the client reads the journal since 2026-09-22
    Then the client is given only the change made today

  @slice-91
  Scenario Outline: Every way the history can be asked for is checked and answered plainly
    Pins that a filter is an input like any other: one that names nothing real gives nothing back and no fault, and one that cannot be read at all is refused rather than breaking off.
    When the client reads the journal <filter>
    Then <outcome>

    Examples:
      | filter                                                  | outcome                                                              |
      | for a set of changes the history holds nothing under    | the client is given no entries and no fault                          |
      | for a role nothing in the history was done under        | the client is given no entries and no fault                          |
      | since something that cannot be read as a moment in time | the read is rejected because since names a moment in time            |

  @slice-91
  Scenario: A change aimed at one place records the place it changed
    Pins that the history says where inside an artifact a change landed, so a reader can tell a change to one section from a change to the whole artifact.
    Given a store where an agent replaced one section of a decision
    When the client reads the journal for that decision
    Then the entry for that change names the place inside the decision that was changed
