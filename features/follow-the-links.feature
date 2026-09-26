Feature: Follow the links
So that a client can show how the store's contents hang together, the client can follow the links.

  Background:
    Given a store where a decision supersedes an older decision
    And two work items point at that decision
    And the older decision is tagged "pricing"

  @slice-31
  Scenario: The client follows the links out of an artifact
    Pins the simplest traversal: what an artifact points at comes back as stubs, enough to show without reading each target whole.
    When the client follows the links out of the decision
    Then the client is given a stub of the older decision

  @slice-31
  Scenario: The client follows the links into an artifact
    Pins that the store knows who points at a thing as well as what it points at, which is the question no single artifact can answer by itself.
    When the client follows the links into the decision
    Then the client is given a stub of each work item

  @slice-31
  Scenario: The client narrows the links to one link and one kind
    Pins that a traversal can be narrowed to one link and one kind, so a client asks its real question instead of filtering everything afterwards.
    Given a note that is not a work item also points at the decision, through the same link the work items use
    And one of the two work items points at the decision a second time, through a different link of its own
    When the client follows the links into the decision, only through the link a work item uses, and only from work items
    Then the client is given both work items and nothing else

  @slice-11
  Scenario: The client follows the links two steps out
    Pins that a traversal can go more than one step and reports the route to each thing found, so a client can explain why something turned up.
    When the client follows the links out of the decision two steps
    Then the client is given the older decision and the tag
    And each of them comes with the route taken to it

  Scenario: The client follows the links out of one place inside an artifact
    Pins that a traversal can start at a place inside an artifact rather than the whole of it, so a client can ask what one section or one step points at and get only that.
    Given the decision's rationale points at a tag of its own
    When the client follows the links out of the rationale of the decision
    Then the client is given a stub of that tag and nothing else the decision points at

  Scenario: A link into a part counts as a link into the artifact holding it
    Pins that pointing at a part is pointing at the artifact it sits in, so the count at a glance, the links coming in, and what blocks a removal all agree with one another.
    Given a store holding a process, and a work item that points at one step of that process rather than at the whole process
    When the client follows the links into the process
    Then the client is given a stub of that work item
    And reading the process at a glance counts that work item among the things pointing at it
    And removing the process is refused while that work item points into it
