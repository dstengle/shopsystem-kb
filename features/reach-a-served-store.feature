# formulated from spec/capabilities/reach-a-served-store.md
Feature: Reach a served store
  Narrator: the client

  Background:
    Given a store holding a decision with a purpose and a rationale, at its first version

  Scenario: A client that reaches a served store makes the same calls and is given the same answers as a client that reaches the store in process
    Pins that a server is only a way of reaching the store: a client that reaches it over the network gets what it would have got in process.
    Given a server serves that store, and the client works where the connection to that server is found
    When the client reads the decision
    Then the client is given what a client that reaches that store in process is given for the same read

  Scenario Outline: A connection to a server that cannot be read or names no address is refused, naming the connection
    Pins that a connection that does not lead anywhere is its own refusal, naming the connection, rather than being guessed at.
    Given the client is working where the connection to a server is found, and that connection <state>
    When the client reads the decision
    Then the read is rejected because the connection cannot be read or names no address, and the connection is named back

    Examples:
      | state            |
      | cannot be read   |
      | names no address |

  Scenario Outline: A server the connection names that cannot be reached is refused, naming the address
    Pins that a server that is not there, or has gone since it last answered, is a fault the client is given naming where it looked, never a call that hangs or breaks off.
    Given the client is working where the connection to a server is found, and <server>
    When the client reads the decision
    Then the read is rejected because the server cannot be reached, and the address is named back

    Examples:
      | server                                                             |
      | no server was ever at the address it names                         |
      | the server at the address it names answered a read and has stopped |

  Scenario: Each change a served store takes is checked against the store as every earlier change left it, in the order the changes arrive
    Pins that a server takes changes one after another, so two clients sharing a store through it can never together leave a link pointing at nothing.
    Given the store also holds a tag nothing points at
    And a server serves that store
    And one client reaching the server is removing the tag while another reaching it is creating a decision that points at it, each saying which role and why
    When the creation of the decision arrives at the server first
    Then the removal is rejected because something still points at it
    And the store holds the tag and the decision that points at it

  Scenario: A client that finds a served store directly can read it
    Pins that serving a store does not shut out a client working in the store itself from reading what it holds.
    Given a server serves that store
    And the client is working in the directory the store sits in
    When the client reads the decision
    Then the client is given the decision

  Scenario: A change asked by a client that finds a served store directly is refused, naming the server's address
    Pins that while a server owns a store, every change goes through that server, and a client that went round it is told where the server is.
    Given a server serves that store
    And the client is working in the directory the store sits in
    When the client replaces the decision, saying which role and why
    Then the change is rejected because the store is served, and the server's address is named back

  Scenario Outline: After the server that served a store has stopped, however it stopped, a change from a client that finds the store directly is not refused as served
    Pins that a store is served only while its server is running, so a server that ended badly never leaves the store shut to changes.
    Given a server served that store and has since stopped, <how>
    And the client is working in the directory the store sits in
    When the client replaces the decision, saying which role and why
    Then the change is not refused because the store is served

    Examples:
      | how                                            |
      | having been stopped by the operator            |
      | its process having been killed without warning |

  Scenario: A change made through a server the operator runs with kb serve is stamped with the moment the machine's clock gives
    Pins that a server the operator runs times every change with its own clock, never with one a client brings.
    Given a server the operator runs with kb serve serves that store, and the client works where the connection to that server is found
    When the client replaces the decision, saying which role and why
    Then every entry that change left in the journal says it happened at the moment the machine's clock gave

  Scenario: A change asked of a server by a client readied with a clock is refused
    Pins that a client's own clock is for a store it reaches in process, so a client cannot set the moment of a change a server makes.
    Given a server serves that store, and the client works where the connection to that server is found
    And the client was readied with a clock that reads 2026-09-23 at 14:30
    When the client replaces the decision, saying which role and why
    Then the change is rejected because the clock belongs to a client that reaches its store in process

  Scenario: The store never writes the connection to a server
    Pins that the connection is only ever written by whoever arranges the callers, so the store and its server never invent or move one.
    Given a server the operator runs with kb serve serves that store, and the client works where the connection to that server is found
    When the client replaces the decision, saying which role and why
    Then the directory the store sits in holds no connection to a server
    And the connection the client reached the server through is left as it was

  Scenario: A client readied with a clock that finds a server has its reads answered
    Pins that the clock refuses only changes: a client that brings a clock can still read through a server.
    Given a server serves that store, and the client works where the connection to that server is found
    And the client was readied with a clock that reads 2026-09-23 at 14:30
    When the client reads the decision
    Then the client is given the decision
