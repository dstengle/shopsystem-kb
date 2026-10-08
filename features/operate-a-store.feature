# formulated from spec/capabilities/operate-a-store.md
Feature: Operate a store
  Narrator: the operator

  @slice-46
  Scenario: The operator sets up a store
    Pins that a store can be brought into being from a shell before any client exists, and is usable the moment it does.
    Given a directory that has no store inside it
    When the operator runs kb init against that directory, saying which role they are
    Then there is a store inside that directory, in a place of its own
    And a client can begin defining its own types in it straight away

  @slice-46
  Scenario: Setting up a store without naming which role is refused
    Pins that every change is attributable from the very first one, so a store cannot be created by nobody.
    Given a directory that has no store inside it, and nothing names which role the operator is
    When the operator runs kb init against that directory
    Then setting the store up is rejected because the role must be named through KB_ACTOR
    And that directory still has no store inside it

  @slice-46
  Scenario: Setting up a store where the directory already has one inside it is refused
    Pins that setting up never writes over what is there: an existing store is left exactly as it was.
    Given a directory that already has a store inside it, with content in that store
    When the operator runs kb init against that directory, saying which role they are
    Then setting the store up is rejected because that directory already has a store inside it
    And the store that is there holds what it held before

  @slice-46
  Scenario: Setting up a store inside a store is refused
    Pins that stores do not nest, so no directory is ever inside two of them and no call has to guess which one it meant.
    Given a directory that sits inside a store
    When the operator runs kb init against that directory, saying which role they are
    Then setting the store up is rejected because that directory is inside a store
    And the store it sits inside holds what it held before

  @slice-138
  Scenario: The operator sets up a store seeded from a directory of files
    Pins that a store can be set up already holding a directory of files, landed exactly as an import into a freshly started store would land them.
    Given a directory that has no store inside it
    And a seed directory that checks clean, holding a type for decisions and a decision
    When the operator runs kb init with that seed directory against the directory, saying which role they are
    Then there is a store inside that directory
    And it holds the files in the seed directory as kb import lands them into a freshly started store

  @slice-140
  Scenario: Setting up a store from a seed directory whose files do not check clean is refused
    Pins that a seed is all or nothing: a seed with any error leaves no store behind, and the operator is shown why.
    Given a directory that has no store inside it
    And a seed directory holding one file whose content does not fit its type
    When the operator runs kb init with that seed directory against the directory, saying which role they are
    Then setting the store up is rejected because the seed directory's files do not check clean
    And the operator is shown the check's report
    And that directory still has no store inside it

  @slice-139
  Scenario: A seeded setup that was stopped before it finished leaves no store, and the same setup run again lands the seed
    Pins that a setup stopped partway, however it was stopped, never leaves a half-seeded store, and nothing it left behind gets in the way of running it again.
    Given a directory that has no store inside it
    And a seed directory that checks clean, holding a type for decisions and a decision
    When the operator's kb init with that seed directory against the directory, saying which role they are, is stopped before it finishes
    Then that directory has no store inside it
    When the operator runs the same kb init again
    Then there is a store inside that directory
    And it holds the files in the seed directory as kb import lands them into a freshly started store

  @slice-140
  Scenario: Setting up a seeded store where the directory already has one inside it is refused
    Pins that a seed never lands over an existing store: the store that is there is left exactly as it was.
    Given a directory that already has a store inside it, with content in that store
    And a seed directory that checks clean
    When the operator runs kb init with that seed directory against the directory, saying which role they are
    Then setting the store up is rejected because that directory already has a store inside it
    And the store that is there holds what it held before

  @slice-140
  Scenario: Setting up a seeded store without naming which role is refused
    Pins that a seeded store, like an empty one, cannot be created by nobody.
    Given a directory that has no store inside it, and nothing names which role the operator is
    And a seed directory that checks clean
    When the operator runs kb init with that seed directory against the directory
    Then setting the store up is rejected because the role must be named through KB_ACTOR
    And that directory still has no store inside it

  @slice-140
  Scenario: Setting up a seeded store inside a store is refused
    Pins that seeding does not make stores nest any more than setting up an empty one does.
    Given a directory that sits inside a store
    And a seed directory that checks clean
    When the operator runs kb init with that seed directory against the directory, saying which role they are
    Then setting the store up is rejected because that directory is inside a store
    And the store it sits inside holds what it held before

  @slice-140
  Scenario: Setting up a store seeded from something that is not a directory is refused
    Pins that a seed is read only from a directory, so a setup pointed at anything else leaves no store behind.
    Given a directory that has no store inside it
    And a file where the seed directory should be
    When the operator runs kb init with that file as the seed directory against the directory, saying which role they are
    Then setting the store up is rejected because files for import are read from a directory
    And that directory still has no store inside it

  @slice-147
  Scenario: The operator sets up a store seeded from the directory it is started in
    Pins that a seed copied into the place a store will live can be landed from there, and that nothing kb makes while starting the store is taken for part of the seed.
    Given a directory that has no store inside it, holding files that check clean: a type for decisions and a decision
    When the operator runs kb init with that same directory as the seed directory against it, saying which role they are
    Then there is a store inside that directory
    And it holds the files the directory held as kb import lands them into a freshly started store, and nothing else

  @slice-146
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

  @slice-46
  Scenario: The operator checks the whole store
    Pins the operator's health check: one command tells them everything that does not fit and everything that has fallen behind, for content they did not write.
    Given a store whose content the operator did not write
    When the operator runs kb validate in that store
    Then the operator is told of everything in the store that does not fit its type, and where
    And of everything that is behind the type it was last checked against

  @slice-113
  Scenario: The command line changes content only by importing into a freshly started store
    Pins the limit of the command line: it sets stores up, checks and exports them, and imports into a freshly started one, and nothing else, because every other change to content goes through a client.
    Given a store
    When the operator asks what the command line offers
    Then it offers setting a store up, checking and exporting one, and importing into a freshly started store
    And nothing else that changes what the store holds

  @slice-46
  Scenario: The operator checks the store from a folder inside it
    Pins that the store is found by looking upward from where the operator stands, so they need not be at its root to use it.
    Given a store, with the operator working in a folder deep inside the directory it sits in
    When the operator runs kb validate there
    Then the store found above where they are working is the one checked

  @slice-46
  Scenario: The operator names the store instead of standing in it
    Pins the other way to say which store is meant, for when the operator is not standing in one.
    Given a store, with the operator working outside any store and KB_ROOT naming that one
    When the operator runs kb validate there
    Then the store KB_ROOT names is the one checked

  @slice-46
  Scenario: Running the command line where no store can be found is refused
    Pins that no store is ever invented or assumed: with nothing above and nothing named, the command says so.
    Given the operator is working outside any store and nothing names one
    When the operator runs kb validate there
    Then the check is rejected because no store was found, neither above where they are working nor named outright

  @slice-46
  Scenario: Naming a store that is not there is refused
    Pins that naming a store wrongly is its own answer, naming KB_ROOT, rather than quietly falling back to searching upward.
    Given the operator is working outside any store, with KB_ROOT naming a directory that holds no store
    When the operator runs kb validate there
    Then the check is rejected because KB_ROOT names a directory that holds no store

  @slice-46
  Scenario: Standing in one store while naming another is refused
    Pins that two answers to which store is meant is a refusal, not a preference, so no check ever runs against a store the operator did not expect.
    Given the operator is working inside a store, with KB_ROOT naming a different store
    When the operator runs kb validate there
    Then the check is rejected because KB_ROOT names a store other than the one they are standing in, and neither of the two is guessed at

  @slice-128
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

  @slice-128
  Scenario: Serving a store without giving an address is refused
    Pins that a store is never served somewhere the operator did not choose: with no address given, nothing is served.
    Given a directory holding a store
    When the operator runs kb serve on that directory without giving an address
    Then serving the store is rejected because no address is assumed

  @slice-128.1
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

  @slice-141
  Scenario: The operator serves a directory holding no store, asking for it to be started first
    Pins that one command can bring a store into being and serve it, so an empty place becomes a served store without a separate setup.
    Given a directory holding no store
    When the operator runs kb serve with --start on that directory, giving an address, saying which role they are
    Then a store is started in that directory
    And that store is served at that address

  @slice-141
  Scenario: Serving with --start a directory that already holds a store serves that store as it stands
    Pins that asking for a start never touches a store that is already there, and needs no role when nothing is started.
    Given a directory holding a store with content in it, and nothing names which role the operator is
    When the operator runs kb serve with --start on that directory, giving an address
    Then that store is served at that address
    And it holds what it held before

  @slice-142
  Scenario: Serving with --start a directory holding no store without naming which role is refused
    Pins that a store started in order to be served is attributable from its first change, like any other.
    Given a directory holding no store, and nothing names which role the operator is
    When the operator runs kb serve with --start on that directory, giving an address
    Then serving is rejected because a store can only be started under a role named through KB_ACTOR
    And nothing is served
    And that directory still holds no store

  @slice-142
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

  @slice-143
  Scenario: Serving with --start a directory that sits inside a store is refused
    Pins that starting a store in order to serve it never makes stores nest.
    Given a directory that sits inside a store
    When the operator runs kb serve with --start on that directory, giving an address, saying which role they are
    Then serving is rejected because that directory is inside a store
    And nothing is served
    And the store it sits inside holds what it held before

  @slice-143
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

  @slice-115
  Scenario: The operator checks the store while another change is being written
    Pins that checking is a read: it goes ahead however long another change holds the store.
    Given a store whose content the operator did not write
    And another change is being written and holds the store longer than the store waits
    When the operator runs kb validate in that store
    Then the store is checked
    And kb validate is not refused because the store was busy with another change
