# formulated from spec/capabilities/keep-the-history.md
Feature: Keep the history
  Narrator: the client

  @slice-9
  Scenario: Every change leaves an entry
    Pins that nothing changes the store unrecorded, and pins exactly what each record carries, since that is the whole of what can ever be asked about the past.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    When the client reads the journal for that decision
    Then there is one entry for each change
    And each entry says when it happened, which role made it, for which piece of work, what it did, to which artifact and place in it, the version it left behind, a fingerprint of what was written, the message given, and which set of changes it landed with

  @slice-35
  Scenario: The journal alone shows what landed together
    Pins that the journal is self-sufficient about grouping: what landed together is visible in the entries themselves, with a lone change its own set, so nothing outside has to be consulted.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    Given a store where two artifacts were changed in one go and a third was changed on its own
    When the client reads the journal
    Then the two entries from the one go name the same set of changes
    And the entry for the change made on its own names itself as its own set
    And the client can tell what landed together from the journal without reading anything else

  @slice-35
  Scenario: The client reads the journal for one role
    Pins the "who did this" question, answered by the journal rather than by the client reading everything.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    When the client reads the journal for the shopkeeper
    Then the client is given only the creation of the decision

  @slice-35
  Scenario: The client reads the journal for one piece of work
    Pins the "what did this piece of work change" question, which is how a run of work is accounted for after the fact.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    When the client reads the journal for that piece of work
    Then the client is given only the change the agent made

  @slice-35
  Scenario: The client reads the journal since a time
    Pins the "what has happened lately" question, so a client can catch up without walking the whole history.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    When the client reads the journal since 2026-09-22
    Then the client is given only the change made today

  @slice-102
  Scenario Outline: A client given a clock stamps each change it makes with the moment the clock gives
    Pins that a client can say when its own changes happen, so its own tests can lay down a history across several days without waiting for them or touching the store's files.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    Given the client was readied with a clock that reads 2026-09-23 at 14:30
    When the client <change>
    Then every entry that change left in the journal says it happened at 2026-09-23 at 14:30

    Examples:
      | change                                            |
      | creates a second decision                         |
      | changes the decision                              |
      | adds an item to one of the decision's collections |
      | removes the decision                              |
      | makes several changes in one go                   |
      | snapshots what a piece of work read               |

  @slice-102.3
  Scenario Outline: Changes stamped with the same moment each leave an entry of their own
    Pins that a clock standing still loses nothing: every change is still recorded, at the moment the clock gave, and changes made apart never share a set just because they share a moment.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    Given the client was readied with a clock that reads 2026-09-23 at 14:30
    And the client has <changes>
    When the client reads the journal
    Then there is one entry for each of those changes, each saying it happened at 2026-09-23 at 14:30
    And each of those changes names itself as its own set, and no two of them name the same set

    Examples:
      | changes                                                                                                                                                                      |
      | changed the decision five times, one change after another                                                                                                                    |
      | created a second decision, changed the decision, added an item to one of the decision's collections, snapshotted what a piece of work read, and removed the second decision |
      | snapshotted what a piece of work read twice                                                                                                                                  |

  @slice-102.3
  Scenario: Sets of changes made at the same moment are told apart
    Pins that the name the store gives a set belongs to that set alone, even when several sets land at the same moment, so what landed together is never confused with what merely landed at the same time.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    Given the client was readied with a clock that reads 2026-09-23 at 14:30
    And the client has made two changes in one go, then one change on its own, then two more changes in another go
    When the client reads the journal
    Then the two entries from the first go name one set, and the two entries from the second go name another
    And the change made on its own names itself as its own set, apart from both
    And the name the client was given for each go finds exactly that go's two changes in the history

  @slice-102.4
  Scenario: A moment the clock gives in another zone is kept as the same moment
    Pins that a client's clock may tell the time in any zone without the history mistaking when a change happened, and that the history tells every time in one zone.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    Given the client was readied with a clock that reads 2026-09-24 at 01:30, five hours ahead of UTC
    And the client has created a second decision
    When the client reads the journal for the second decision
    Then the entry for its creation says it happened at the same moment as 2026-09-23 at 20:30 UTC
    And the entry gives that moment in UTC, as 2026-09-23 at 20:30

  @slice-102.4
  Scenario: A moment the clock gives with no zone is recorded as that moment in UTC
    Pins that a clock which does not say its zone is read the way every time a client gives is read, as UTC, so the history never holds a time that cannot be placed.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    Given the client was readied with a clock that reads 2026-09-23 at 20:30, with no zone
    And the client has created a second decision
    When the client reads the journal for the second decision
    Then the entry for its creation says it happened at 2026-09-23 at 20:30, given in UTC

  @slice-102.4
  Scenario Outline: The history read since a time answers plainly whatever zone the clock gave
    Pins that a history holding moments given in another zone, or in none, is still read plainly: asking what has happened since a time answers by the moment itself, not the way the clock wrote it, and never breaks off.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    Given the client was readied with a clock that reads <reading>
    And the client has created a second decision
    When the client reads the journal for the second decision since <moment>
    Then <outcome>

    Examples:
      | reading                                      | moment                                       | outcome                                                 |
      | 2026-09-24 at 01:30, five hours ahead of UTC | 2026-09-23 at 20:00 UTC                      | the client is given the creation of the second decision |
      | 2026-09-24 at 01:30, five hours ahead of UTC | 2026-09-23 at 21:00 UTC                      | the client is given no entries and no fault             |
      | 2026-09-24 at 01:30, five hours ahead of UTC | 2026-09-24 at 01:00, five hours ahead of UTC | the client is given the creation of the second decision |
      | 2026-09-24 at 01:30, five hours ahead of UTC | 2026-09-24 at 02:00, five hours ahead of UTC | the client is given no entries and no fault             |
      | 2026-09-23 at 20:30, with no zone            | 2026-09-23 at 20:00 UTC                      | the client is given the creation of the second decision |
      | 2026-09-23 at 20:30, with no zone            | 2026-09-23 at 21:00 UTC                      | the client is given no entries and no fault             |

  @slice-91
  Scenario Outline: Every way the history can be asked for is checked and answered plainly
    Pins that a filter is an input like any other: one that names nothing real gives nothing back and no fault, and one that cannot be read at all is refused rather than breaking off.
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
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
    Given today is 2026-09-23
    And a store where the shopkeeper created a decision on 2026-09-21 and an agent working on a named piece of work changed it today
    Given a store where an agent replaced one section of a decision
    When the client reads the journal for that decision
    Then the entry for that change names the place inside the decision that was changed

  @slice-102.3
  Scenario: Starting a store and the first change after it keep separate entries at the same moment
    Pins that the first entry in a history is never lost to the change that follows it, however close together the client's clock puts them.
    Given a store the client started, readied with a clock that reads 2026-09-20 at 08:00
    When the client defines its own type
    Then the store's history holds two entries, both saying they happened at 2026-09-20 at 08:00
    And each names itself as its own set
