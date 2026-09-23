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

  @slice-20
  Scenario: The client reads one section by its title
    When the client reads the rationale of the decision
    Then the client is given that section and nothing else

  @slice-20
  Scenario: The client reads the whole artifact
    When the client reads the whole decision
    Then the client is given every field, every section and every part, in the order the type declares

  Scenario: Without being asked to follow them, links come back as names
    When the client reads the whole decision without asking for its links to be followed
    Then the older decision is given as the name it is known by, and nothing more

  @slice-20
  Scenario: The client reads the whole artifact with what it points at filled in
    When the client reads the whole decision following its links one step
    Then the older decision is given in place of the link, as the store holds it now
    And what the older decision itself points at is given as names

  Scenario: The client reads an artifact following its links two steps
    Given the older decision is tagged "pricing"
    When the client reads the whole decision following its links two steps
    Then the older decision is given in place of the link
    And the tag is given in place of the link inside the older decision

  Scenario: A loop in the links stops instead of going round
    Given two decisions that point at each other
    When the client reads the whole of one of them following its links three steps
    Then the other decision is given in place of the link
    And where that one points back, the decision being read is given as a name rather than filled in again

  Scenario: The branches inside a process are not followed
    Given a store holding a process whose steps branch to other steps of the same process
    When the client reads the whole process following its links one step
    Then the branches are given as written, naming the steps of that process
