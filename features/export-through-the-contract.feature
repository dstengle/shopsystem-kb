# formulated from spec/capabilities/export-through-the-contract.md
Feature: Export through the contract
  Narrator: the client

  @slice-172 @r1
  Scenario: The client exports the store
    Pins what an export through the contract gives: every canonical file of the store, one at a time, each at the place its artifact's IRI gives it, all from one moment, with the position in the history they reflect.
    Given a store holding a type for decisions, a type for work items, two decisions and a work item
    When the client exports the store
    Then the client is given the store's canonical files one at a time
    And each file comes with the place that follows its artifact's IRI
    And every file shows the store as it stood at one moment
    And the client is told the position in the history those files reflect

  @slice-172 @r2
  Scenario: The client exports the store, and is told the position of the last history entry landed at that moment
    Pins which position an export reports: that of the last history entry landed when the store stood at the export's moment, so the client knows exactly what the files include.
    Given a store holding a decision, whose replacement is the last entry landed in its history
    When the client exports the store
    Then the position the client is told is the position of the history entry the decision's replacement landed
    And the decision's file shows the decision as that replacement left it

  @slice-174 @r3
  Scenario: The client exports a store holding several versions of a type
    Pins that every version of a type the store holds comes out as a file of its own, placed at the type's place followed by the version's number.
    Given a store holding a type for decisions at its third version
    When the client exports the store
    Then the client is given one file for each of the three versions of the type for decisions
    And each of those files is at the type's place, followed by `@` and that version's number

  @slice-176 @r4
  Scenario: The client exports selecting a path below the type
    Pins that a path selects by whole segments from the start of the path below each artifact's type, across every type, and nothing else.
    Given a store holding a decision whose path below its type is "adr/2026/first", a work item whose path below its type is "adr/2026/review", a decision whose path below its type is "adr/2026-old/second" and a decision whose path below its type is "notes/adr/2026/third"
    When the client exports selecting the path "adr/2026"
    Then the client is given the files of the decision at "adr/2026/first" and the work item at "adr/2026/review"
    And the client is given no other file

  @slice-176 @r5
  Scenario: The client exports selecting a type
    Pins that a type selects only the files of the artifacts of that type.
    Given a store holding a type for decisions, a type for work items, two decisions and a work item
    When the client exports selecting the type for decisions
    Then the client is given the files of the two decisions
    And the client is given no other file

  @slice-176 @r6
  Scenario: The client exports selecting a path below the type and a type together
    Pins that a path and a type selected together narrow each other: only that type's artifacts whose path below the type begins with the segments given.
    Given a store holding a decision whose path below its type is "adr/2026/first", a work item whose path below its type is "adr/2026/review" and a decision whose path below its type is "notes/second"
    When the client exports selecting the path "adr/2026" and the type for decisions together
    Then the client is given the file of the decision at "adr/2026/first"
    And the client is given no other file

  @slice-173 @r7
  Scenario: While a server serves the store, the client exports through it
    Pins that an export through a server is the same export a client gets in process: the same files and the same position.
    Given a store holding a type for decisions and two decisions
    And a server serves that store, and the client works where the connection to that server is found
    When the client exports the store through the server
    Then the client is given the same files, at the same places, as a client that reaches that store in process is given
    And the client is told the same position as a client that reaches that store in process is told

  @slice-173 @r8
  Scenario: While another change is being written to the store, the client exports it
    Pins that an export is a read: it is given however long another change holds the store.
    Given a store holding a decision
    And another change is being written and holds the store longer than the store waits
    When the client exports the store
    Then the client is given the export
    And the export is not refused because the store was busy with another change
