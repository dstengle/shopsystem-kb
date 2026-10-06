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

  Scenario: Serving a store without giving an address is refused
    Pins that a store is never served somewhere the operator did not choose: with no address given, nothing is served.
    Given a directory holding a store
    When the operator runs kb serve on that directory without giving an address
    Then serving the store is rejected because no address is assumed

  @slice-115
  Scenario: The operator checks the store while another change is being written
    Pins that checking is a read: it goes ahead however long another change holds the store.
    Given a store whose content the operator did not write
    And another change is being written and holds the store longer than the store waits
    When the operator runs kb validate in that store
    Then the store is checked
    And kb validate is not refused because the store was busy with another change
