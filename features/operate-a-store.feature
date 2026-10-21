# formulated from spec/capabilities/operate-a-store.md
Feature: Operate a store
  Narrator: the operator

  @slice-46 @r1
  Scenario: The operator sets up a store
    Pins that a store can be brought into being from a shell before any client exists, and is usable the moment it does.
    Given a directory that has no store inside it
    When the operator runs kb init against that directory, saying which role they are
    Then there is a store inside that directory, in a place of its own
    And a client can begin defining its own types in it straight away

  @slice-46 @r2
  Scenario: Setting up a store without naming which role is refused
    Pins that every change is attributable from the very first one, so a store cannot be created by nobody.
    Given a directory that has no store inside it, and nothing names which role the operator is
    When the operator runs kb init against that directory
    Then setting the store up is rejected because the role must be named through KB_ACTOR
    And that directory still has no store inside it

  @slice-46 @r3
  Scenario: Setting up a store where the directory already has one inside it is refused
    Pins that setting up never writes over what is there: an existing store is left exactly as it was.
    Given a directory that already has a store inside it, with content in that store
    When the operator runs kb init against that directory, saying which role they are
    Then setting the store up is rejected because that directory already has a store inside it
    And the store that is there holds what it held before

  @slice-46 @r4
  Scenario: Setting up a store inside a store is refused
    Pins that stores do not nest, so no directory is ever inside two of them and no call has to guess which one it meant.
    Given a directory that sits inside a store
    When the operator runs kb init against that directory, saying which role they are
    Then setting the store up is rejected because that directory is inside a store
    And the store it sits inside holds what it held before

  @slice-138 @r5
  Scenario: The operator sets up a store seeded from a directory of files
    Pins that a store can be set up already holding a directory of files, landed exactly as an import into a freshly started store would land them.
    Given a directory that has no store inside it
    And a seed directory that checks clean, holding a type for decisions and a decision
    When the operator runs kb init with that seed directory against the directory, saying which role they are
    Then there is a store inside that directory
    And it holds the files in the seed directory as kb import lands them into a freshly started store

  @slice-140 @r6
  Scenario: Setting up a store from a seed directory whose files do not check clean is refused
    Pins that a seed is all or nothing: a seed with any error leaves no store behind, and the operator is shown why.
    Given a directory that has no store inside it
    And a seed directory holding one file whose content does not fit its type
    When the operator runs kb init with that seed directory against the directory, saying which role they are
    Then setting the store up is rejected because the seed directory's files do not check clean
    And the operator is shown the check's report
    And that directory still has no store inside it

  @slice-139 @r7
  Scenario: A seeded setup that was stopped before it finished leaves no store, and the same setup run again lands the seed
    Pins that a setup stopped partway, however it was stopped, never leaves a half-seeded store, and nothing it left behind gets in the way of running it again.
    Given a directory that has no store inside it
    And a seed directory that checks clean, holding a type for decisions and a decision
    When the operator's kb init with that seed directory against the directory, saying which role they are, is stopped before it finishes
    Then that directory has no store inside it
    When the operator runs the same kb init again
    Then there is a store inside that directory
    And it holds the files in the seed directory as kb import lands them into a freshly started store

  @slice-140 @r8
  Scenario: Setting up a seeded store where the directory already has one inside it is refused
    Pins that a seed never lands over an existing store: the store that is there is left exactly as it was.
    Given a directory that already has a store inside it, with content in that store
    And a seed directory that checks clean
    When the operator runs kb init with that seed directory against the directory, saying which role they are
    Then setting the store up is rejected because that directory already has a store inside it
    And the store that is there holds what it held before

  @slice-140 @r9
  Scenario: Setting up a seeded store without naming which role is refused
    Pins that a seeded store, like an empty one, cannot be created by nobody.
    Given a directory that has no store inside it, and nothing names which role the operator is
    And a seed directory that checks clean
    When the operator runs kb init with that seed directory against the directory
    Then setting the store up is rejected because the role must be named through KB_ACTOR
    And that directory still has no store inside it

  @slice-140 @r10
  Scenario: Setting up a seeded store inside a store is refused
    Pins that seeding does not make stores nest any more than setting up an empty one does.
    Given a directory that sits inside a store
    And a seed directory that checks clean
    When the operator runs kb init with that seed directory against the directory, saying which role they are
    Then setting the store up is rejected because that directory is inside a store
    And the store it sits inside holds what it held before

  @slice-140 @r11
  Scenario: Setting up a store seeded from something that is not a directory is refused
    Pins that a seed is read only from a directory, so a setup pointed at anything else leaves no store behind.
    Given a directory that has no store inside it
    And a file where the seed directory should be
    When the operator runs kb init with that file as the seed directory against the directory, saying which role they are
    Then setting the store up is rejected because files for import are read from a directory
    And that directory still has no store inside it

  @slice-148 @r12
  Scenario Outline: The operator sets up a store seeded from a directory that is, or holds, the directory it is started in
    Pins that a seed copied into, or around, the place a store will live can be landed from there, and that nothing kb makes while starting the store is taken for part of the seed.
    Given a directory that has no store inside it
    And a seed directory that <relation> that directory, holding files that check clean: a type for decisions and a decision
    When the operator runs kb init with that seed directory against the directory, saying which role they are
    Then there is a store inside that directory
    And it holds the files the seed directory held as kb import lands them into a freshly started store, and nothing else

    Examples:
      | relation |
      | is       |
      | holds    |

  @slice-146 @r13
  Scenario Outline: Starting a store in a directory kb cannot write is refused
    Pins that a directory kb cannot write is told apart from a store that cannot answer: the operator is told the directory cannot be written, and nothing is made in it.
    Given a directory that has no store inside it and that kb cannot write
    When the operator runs <command> against that directory, saying which role they are
    Then starting the store is rejected because a store can only be started in a directory kb can write, and the directory is named
    And nothing is served
    And that directory still has nothing made in it

    Examples:
      | command                                  |
      | kb init                                  |
      | kb init with a seed directory            |
      | kb serve with --start, giving an address |

  @slice-170 @r14
  Scenario: The operator checks the whole store
    Pins the operator's health check: one command tells them what does not fit, what has fallen behind, and what is linked to but not held, down to each link they would fill, without mixing the three.
    Given a store whose content the operator did not write
    And it holds a decision that does not fit its type
    And it holds a decision that conforms to a version of its type a later version has followed
    And it holds a decision linking twice to a work item the store does not hold, under a type for work items it holds, from two different places in that decision
    When the operator runs kb validate in that store
    Then the operator is told of the decision that does not fit its type, and where
    And of the decision behind the type it conforms to
    And of the work item linked to and not held, a placeholder, with each of the two links into it: the decision holding the link and the place in that decision the link sits at
    And each of the three is listed apart from the others

  @slice-170 @r15
  Scenario: The operator checks a store whose only findings are placeholders
    Pins that a placeholder is never a fault: a store holding nothing wrong but links to what it does not hold passes the operator's check.
    Given a store holding a type for decisions, a type for work items, and a decision that fits its type
    And that decision links to a work item the store does not hold
    And nothing else in the store does not fit its type or is behind it
    When the operator runs kb validate in that store
    Then the store checks clean

  @slice-185 @r16
  Scenario: The command line offers setting up, checking, exporting, backing up, restoring and importing, and nothing else that changes what the store holds
    Pins the limit of the command line: import is offered into a store, not only a freshly started one, and every other change to content still goes through a client.
    Given a store
    When the operator asks what the command line offers
    Then it offers setting a store up, checking and exporting one, backing one up, restoring a backup, and importing into a store
    And nothing else that changes what the store holds

  @slice-149 @r17
  Scenario: The operator backs up a store, and the backup holds it whole
    Pins that a backup leaves nothing of the store behind: not only what it holds now, but how each thing came to be and every entry of its journal.
    Given a store holding a type for decisions and two decisions, one of them replaced since it was made
    And a piece of work has snapshotted what it read
    When the operator backs up the store
    Then the backup holds everything the store holds
    And it holds the history of each decision
    And it holds every entry of the store's journal, the snapshot included

  @slice-150 @r18
  Scenario: A set landing while the operator backs up the store is in the backup whole or not at all
    Pins that a backup is the store at one moment: a set that lands while it is made is never found in it in part.
    Given a store holding a type for decisions
    And a client is landing a set that makes three decisions
    When the operator backs up the store while that set is landing
    Then the backup holds either all three decisions of that set, with their history and journal entries, or none of them

  @slice-150 @r19
  Scenario: The operator backs up the store while clients are writing to it
    Pins that backing up a running store does not stop its writers: they are never turned away because a backup is being made.
    Given a store holding a type for decisions
    And clients are writing decisions to the store
    When the operator backs up the store
    Then the backup is made
    And the clients go on writing
    And none of their changes is refused because of the backup

  @slice-150 @r20
  Scenario: The operator backs up the store while another change is being written
    Pins that a backup goes ahead however long another change holds the store.
    Given a store holding a type for decisions and a decision
    And another change is being written and holds the store longer than the store waits
    When the operator backs up the store
    Then the backup is made
    And the backup is not refused because the store was busy with another change

  @slice-150 @r21
  Scenario: The operator backs up a store a server is serving
    Pins that a served store can be backed up without stopping its server.
    Given a store holding a type for decisions and a decision
    And a server serves that store
    When the operator backs up the store
    Then the backup is made
    And the server goes on serving: a caller reaching it is answered from that store

  @slice-153 @r22
  Scenario Outline: Backing up a store to a place where anything already is is refused
    Pins that a backup never writes over anything, however little is there: even an empty file or an empty directory turns it away untouched.
    Given a store holding a type for decisions and a decision
    And <what is there> at the place the backup would be written
    When the operator backs up the store to that place
    Then the backup is rejected because a backup never overwrites
    And what is at that place is left as it was

    Examples:
      | what is there                 |
      | a file holding something      |
      | an empty file                 |
      | an empty directory            |
      | a directory holding something |

  @slice-153 @r23
  Scenario Outline: kb backup finds the store as kb validate does, and is refused where kb validate is
    Pins that the operator's backup finds a store by the same rules as the operator's check and turns away the same situations, so the two never disagree about which store is meant or whether it can be read.
    Given <where the operator works>
    When the operator runs kb backup there
    Then <outcome>

    Examples:
      | where the operator works                                                  | outcome                                                                         |
      | a folder deep inside the directory a store sits in                        | the store kb validate would check there is the one backed up                    |
      | outside any store, with KB_ROOT naming a store                            | the store kb validate would check there is the one backed up                    |
      | outside any store, with nothing naming one                                | the backup is rejected for the same reason kb validate, run there, is rejected  |
      | outside any store, with KB_ROOT naming a directory that holds no store    | the backup is rejected for the same reason kb validate, run there, is rejected  |
      | inside one store, with KB_ROOT naming a different store                   | the backup is rejected for the same reason kb validate, run there, is rejected  |
      | inside a store made by an earlier kb                                      | the backup is rejected for the same reason kb validate, run there, is rejected  |
      | inside a store made by a later kb                                         | the backup is rejected for the same reason kb validate, run there, is rejected  |
      | inside a store whose database cannot be read                              | the backup is rejected for the same reason kb validate, run there, is rejected  |

  @slice-153 @r24
  Scenario: Backing up where a connection to a server is found and no store is refused
    Pins that a backup is taken from the store's own files, never through a server, so standing beside a connection is not enough to back up the store it reaches.
    Given the operator is working in a directory holding a connection to a server and no store
    And that server serves a store
    When the operator runs kb backup there
    Then the backup is rejected because a backup is made where the store's files are, not through a server

  @slice-149 @r25
  Scenario: The operator restores a backup in a directory with no store inside it
    Pins that a backup comes back as the store it was, nothing left out, and that restoring needs no role because it makes no change of its own.
    Given a backup of a store holding a type for decisions and two decisions, one of them replaced since it was made, and a snapshot of what a piece of work read
    And a directory that has no store inside it, and nothing names which role the operator is
    When the operator restores that backup in that directory
    Then there is a store inside that directory
    And it holds everything the store backed up held
    And it holds the history of each decision
    And it holds every entry of the backed-up store's journal, the snapshot included

  @slice-149 @r26
  Scenario: A restored store's history ends where the backed-up store's did
    Pins that restoring adds nothing to the history: the restored store goes on from exactly where the store stood when it was backed up.
    Given a backup of a store whose last entry is the replacing of a decision
    And a directory that has no store inside it
    When the operator restores that backup in that directory
    Then the restored store's history ends with the replacing of that decision

  @slice-151 @r27
  Scenario: Restoring a backup where the directory already has a store inside it is refused
    Pins that a restore never writes over what is there: an existing store is left exactly as it was.
    Given a backup of a store
    And a directory that already has a store inside it, with content in that store
    When the operator restores that backup in that directory
    Then restoring is rejected because that directory already has a store inside it
    And the store that is there holds what it held before

  @slice-151 @r28
  Scenario: Restoring a backup inside a store is refused
    Pins that restoring does not make stores nest any more than setting one up does.
    Given a backup of a store
    And a directory that sits inside a store
    When the operator restores that backup in that directory
    Then restoring is rejected because that directory is inside a store
    And the store it sits inside holds what it held before

  @slice-151 @r29
  Scenario: Restoring a backup in a directory kb cannot write is refused
    Pins that the operator is told the directory cannot be written, and which one, and that nothing is left in it.
    Given a backup of a store
    And a directory that has no store inside it and that kb cannot write
    When the operator restores that backup in that directory
    Then restoring is rejected because a store can only be restored in a directory kb can write, and the directory is named
    And that directory still has nothing made in it

  @slice-151 @r30
  Scenario: Restoring something that is not a backup kb made is refused
    Pins that only a backup kb made becomes a store: anything else is turned away with nothing left behind.
    Given a file that is not a backup kb made
    And a directory that has no store inside it
    When the operator restores that file in that directory
    Then restoring is rejected because it is not a backup
    And that directory still has nothing made in it

  @slice-151 @r31
  Scenario: Restoring a backup made by an earlier kb is refused
    Pins that a backup this kb cannot read as a store is never restored as one.
    Given a backup made by an earlier kb
    And a directory that has no store inside it
    When the operator restores that backup in that directory
    Then restoring is rejected because this kb cannot read a store an earlier kb made
    And that directory still has nothing made in it

  @slice-151 @r32
  Scenario: Restoring a backup made by a later kb is refused
    Pins that a backup from a newer kb is never restored by an older one, and the operator is told a later kb is needed.
    Given a backup made by a later kb
    And a directory that has no store inside it
    When the operator restores that backup in that directory
    Then restoring is rejected because a later version of kb is needed to read it
    And that directory still has nothing made in it

  @slice-152 @r33
  Scenario: A restore that was stopped before it finished leaves no store, and the same restore run again restores the backup
    Pins that a restore stopped partway, however it was stopped, never leaves a half-restored store, and nothing it left behind gets in the way of running it again.
    Given a backup of a store holding a type for decisions and a decision
    And a directory that has no store inside it
    When the operator's restore of that backup in that directory is stopped before it finishes
    Then that directory has no store inside it
    When the operator runs the same restore again
    Then there is a store inside that directory
    And it holds everything the store backed up held, its history and its journal included

  @slice-46 @r34
  Scenario: The operator checks the store from a folder inside it
    Pins that the store is found by looking upward from where the operator stands, so they need not be at its root to use it.
    Given a store, with the operator working in a folder deep inside the directory it sits in
    When the operator runs kb validate there
    Then the store found above where they are working is the one checked

  @slice-46 @r35
  Scenario: The operator names the store instead of standing in it
    Pins the other way to say which store is meant, for when the operator is not standing in one.
    Given a store, with the operator working outside any store and KB_ROOT naming that one
    When the operator runs kb validate there
    Then the store KB_ROOT names is the one checked

  @slice-46 @r36
  Scenario: Running the command line where no store can be found is refused
    Pins that no store is ever invented or assumed: with nothing above and nothing named, the command says so.
    Given the operator is working outside any store and nothing names one
    When the operator runs kb validate there
    Then the check is rejected because no store was found, neither above where they are working nor named outright

  @slice-46 @r37
  Scenario: Naming a store that is not there is refused
    Pins that naming a store wrongly is its own answer, naming KB_ROOT, rather than quietly falling back to searching upward.
    Given the operator is working outside any store, with KB_ROOT naming a directory that holds no store
    When the operator runs kb validate there
    Then the check is rejected because KB_ROOT names a directory that holds no store

  @slice-46 @r38
  Scenario: Standing in one store while naming another is refused
    Pins that two answers to which store is meant is a refusal, not a preference, so no check ever runs against a store the operator did not expect.
    Given the operator is working inside a store, with KB_ROOT naming a different store
    When the operator runs kb validate there
    Then the check is rejected because KB_ROOT names a store other than the one they are standing in, and neither of the two is guessed at

  @slice-128 @r39
  Scenario Outline: The operator serves a store at the address they give
    Pins that the store is served exactly where the operator says, whether that address names one of the machine's interfaces or all of them.
    Given a directory holding a store
    When the operator runs kb serve on that directory, giving an address on <interface>
    Then the store is served at that address
    And a caller reaching that address through <reached through> is answered from that store

    Examples:
      | interface                      | reached through                     |
      | one interface of the machine   | that interface                      |
      | every interface of the machine | any one of the machine's interfaces |

  @slice-128 @r40
  Scenario: Serving a store without giving an address is refused
    Pins that a store is never served somewhere the operator did not choose: with no address given, nothing is served.
    Given a directory holding a store
    When the operator runs kb serve on that directory without giving an address
    Then serving the store is rejected because no address is assumed

  @slice-128.1 @r41
  Scenario Outline: Serving a store at an address it cannot be served at is refused
    Pins that a store is served exactly where the operator says or not at all, never at some other port and never with the command breaking off.
    Given a directory holding a store
    When the operator runs kb serve on that directory, giving <address>
    Then serving the store is rejected because the store cannot be served at that address, and the address is named back
    And nothing is served

    Examples:
      | address                                  |
      | an address that names no port            |
      | an address whose port is beyond the last |
      | an address another server already holds  |

  @slice-141 @r42
  Scenario: The operator serves a directory holding no store, asking for it to be started first
    Pins that one command can bring a store into being and serve it, so an empty place becomes a served store without a separate setup.
    Given a directory holding no store
    When the operator runs kb serve with --start on that directory, giving an address, saying which role they are
    Then a store is started in that directory
    And that store is served at that address

  @slice-141 @r43
  Scenario: Serving with --start a directory that already holds a store serves that store as it stands
    Pins that asking for a start never touches a store that is already there, and needs no role when nothing is started.
    Given a directory holding a store with content in it, and nothing names which role the operator is
    When the operator runs kb serve with --start on that directory, giving an address
    Then that store is served at that address
    And it holds what it held before

  @slice-142 @r44
  Scenario: Serving with --start a directory holding no store without naming which role is refused
    Pins that a store started in order to be served is attributable from its first change, like any other.
    Given a directory holding no store, and nothing names which role the operator is
    When the operator runs kb serve with --start on that directory, giving an address
    Then serving is rejected because a store can only be started under a role named through KB_ACTOR
    And nothing is served
    And that directory still holds no store

  @slice-142 @r45
  Scenario Outline: Serving with --start a directory holding no store at an address it cannot be served at is refused
    Pins that a store is never left started behind a serve that failed: an address refused leaves the directory as empty as it was.
    Given a directory holding no store
    When the operator runs kb serve with --start on that directory, giving <address>, saying which role they are
    Then serving is rejected because the store cannot be served at that address, and the address is named back
    And nothing is served
    And that directory still holds no store

    Examples:
      | address                                  |
      | an address that names no port            |
      | an address whose port is beyond the last |
      | an address another server already holds  |

  @slice-143 @r46
  Scenario: Serving with --start a directory that sits inside a store is refused
    Pins that starting a store in order to serve it never makes stores nest.
    Given a directory that sits inside a store
    When the operator runs kb serve with --start on that directory, giving an address, saying which role they are
    Then serving is rejected because that directory is inside a store
    And nothing is served
    And the store it sits inside holds what it held before

  @slice-143 @r47
  Scenario Outline: Serving with --start is refused wherever serving without it is refused
    Pins that asking for a start changes only what happens where no store is: everywhere kb serve would refuse, kb serve with --start refuses the same way.
    Given <directory>
    When the operator runs kb serve with --start on that directory, giving <address>, saying which role they are
    Then serving is rejected for the same reason kb serve without --start, run there at that address, is rejected

    Examples:
      | directory                                                 | address                         |
      | a directory holding a store                               | an address that names no port   |
      | a directory holding a store another server owns           | an address nothing else holds   |
      | a directory holding a store made by an earlier kb         | an address nothing else holds   |
      | a directory holding a store made by a later kb            | an address nothing else holds   |
      | a directory holding a connection to a server and no store | an address nothing else holds   |

  @slice-115 @r48
  Scenario: The operator checks the store while another change is being written
    Pins that checking is a read: it goes ahead however long another change holds the store.
    Given a store whose content the operator did not write
    And another change is being written and holds the store longer than the store waits
    When the operator runs kb validate in that store
    Then the store is checked
    And kb validate is not refused because the store was busy with another change
