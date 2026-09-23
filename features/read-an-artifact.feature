Feature: Read an artifact
So that a client can show what the store holds at whatever depth it needs, the client can read an artifact.

  Background:
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items

  @slice-1
  Scenario: The client reads a summary
    When the client reads the decision at a glance
    Then the client is given its name, its kind, its title and the few fields the type shows at a glance
    And a stub of each thing it points at and of each of its parts
    And how many things point at it, counted by their kind and by the link they use

  @slice-22
  Scenario: The client reads one section by its title
    When the client reads the rationale of the decision
    Then the client is given that section and nothing else

  @slice-20
  Scenario: The client reads the whole artifact
    When the client reads the whole decision
    Then the client is given every field, every section and every part, in the order the type declares

  @slice-24
  Scenario: The client reads the whole artifact with what it points at filled in
    When the client reads the whole decision with its links resolved
    Then the older decision is given in place of the link, as the store holds it now
