# formulated from spec/capabilities/snapshot-what-work-read.md
Feature: Snapshot what work read
  Narrator: the client

  Background:
    Given a store holding a decision at its third version and a process at its first

  @slice-37
  Scenario: The client snapshots what a piece of work read
    Pins how one moving store is reconciled with reproducible work: the piece of work records the versions it read, in one history entry it is handed the name of.
    When the client snapshots the decision and the process for a piece of work
    Then the journal holds one entry listing each of them with the version read and a fingerprint of it
    And the client is given the name of that entry

  @slice-93
  Scenario Outline: Every way a snapshot can be asked for wrongly is refused
    Pins that a snapshot is checked like any other call before anything is recorded, so the history never gains an entry attributable to nobody or naming something the store does not hold.
    When the client snapshots <request>
    Then the snapshot is rejected because <reason>
    And the journal holds no entry for it

    Examples:
      | request                                                             | reason                                                                     |
      | the decision and the process without naming the piece of work       | a snapshot records what a named piece of work read                         |
      | the decision and an artifact the store holds nothing under          | the store holds nothing by that name, and the name asked for is given back |
      | the decision and the process without saying which role it is        | every entry in the history names the role that made it                     |
      | the decision and the process without saying why                     | every entry in the history says why it was made                            |
      | the decision and the process giving a role that is only blank space | every entry in the history names the role that made it                     |
      | the decision and the process giving as its reason only blank space  | every entry in the history says why it was made                            |

  @slice-115
  Scenario: A snapshot that waits longer than the store waits for another change is refused as busy
    Pins that a snapshot, which writes a history entry, can be refused as busy like a change, and leaves no entry behind.
    Given another change is being written and holds the store longer than the store waits
    When the client snapshots the decision and the process for a piece of work
    Then the snapshot is rejected because the store was busy with another change
    And the journal holds no entry for it
    And the same snapshot may be asked for again
