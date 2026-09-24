Feature: Start a store
So that a client has somewhere to keep typed artifacts before it has any types of its own, the client can start a store.

  @slice-1
  Scenario: The client starts a store
    Pins what a brand new store contains: the one type that describes types, and nothing of any domain, so the store knows nothing until a client teaches it.
    Given an empty directory
    When the client starts a store there, saying which role it is
    Then the store holds the one type that describes what a type is
    And the store holds no other type and no content
    And the client can define its own types straight away

  @slice-57
  Scenario: Starting a store is recorded in the store's history
    Pins that the history begins with the store itself: even the first thing written is attributed and accounted for like every change after it.
    Given an empty directory
    When the client starts a store there, saying which role it is
    Then the store's history holds one entry, under that role, with the message "initialise store"
    And that entry is the writing of the one type that describes what a type is, at its first version, with a fingerprint of what was written

  @slice-63
  Scenario: Starting a store without saying which role is refused
    Pins that there is no unattributed change anywhere, so a store cannot come into being without someone answering for it.
    Given an empty directory
    When the client starts a store there without saying which role it is
    Then starting the store is rejected because a store can only be started under a role
    And that directory holds no store

  @slice-51
  Scenario: A directory holding other things can still be given a store
    Pins that the store keeps to its own corner of the directory it is given, so it can live alongside a project without claiming any of it.
    Given a directory holding files that have nothing to do with a store
    When the client starts a store there, saying which role it is
    Then the store is made inside that directory, in a place of its own
    And the files that were already there are left as they were, and none of them is the store's concern

  @slice-51
  Scenario: Starting a store in a directory that already has one inside it is refused
    Pins that starting a store never writes over one, so an existing store cannot be lost to a repeated command.
    Given a directory that already has a store inside it, with content in that store
    When the client starts a store there, saying which role it is
    Then starting the store is rejected because that directory already has a store inside it
    And the store that is there holds what it held before

  @slice-50
  Scenario: Starting a store inside a store is refused
    Pins that stores do not nest, so looking upward for a store can only ever find one.
    Given a directory that sits inside a store
    When the client starts a store there, saying which role it is
    Then starting the store is rejected because that directory is inside a store
    And the store it sits inside holds what it held before

  @slice-69
  Scenario: Where a store is started is settled by the directory named, not by where the client is working
    Pins that starting a store is the one call that does not look around for a store: it goes where it is told, and leaves the client's own store alone.
    Given the client is working inside a store
    And an empty directory elsewhere that sits inside no store
    When the client starts a store in that empty directory, saying which role it is
    Then the store is made in the directory the client named
    And the store the client was working in is left as it was

  Scenario: Starting a store without naming a directory at all is refused
    Pins that the directory is an input checked like any other, so an empty one is refused outright rather than falling back on somewhere convenient.
    Given the client has nothing at all to name as the directory to start a store in
    When the client starts a store naming nothing, saying which role it is
    Then starting the store is rejected because a store is started in a directory that was named and that exists
    And no store is made anywhere

  Scenario: Starting a store in a directory that is not there is refused
    Pins that the directory must already exist: the store settles in where it is put and does not build a tree on the way.
    Given a place on the disk where no directory exists
    When the client starts a store there, saying which role it is
    Then starting the store is rejected because a store is started in a directory that exists
    And nothing is made at that place

  Scenario: Starting a store where a file sits instead of a directory is refused
    Pins that what was named must be a directory, and that a file standing in that place is left untouched rather than written through.
    Given a place on the disk holding a file rather than a directory
    When the client starts a store there, saying which role it is
    Then starting the store is rejected because a store is started in a directory, and what was named is not one
    And that file is left as it was
