Feature: Snapshot what a piece of work read
So that a piece of work can say which versions it was built on while the store keeps moving, the client can snapshot what a piece of work read.

  Background:
    Given a store holding a decision at its third version and a process at its first

  @slice-36
  Scenario: The client snapshots what a piece of work read
    Pins how one moving store is reconciled with reproducible work: the piece of work records the versions it read, in one history entry it is handed the name of.
    When the client snapshots the decision and the process for a piece of work
    Then the journal holds one entry listing each of them with the version read and a fingerprint of it
    And the client is given the name of that entry
