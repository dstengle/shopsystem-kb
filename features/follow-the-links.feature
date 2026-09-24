Feature: Follow the links
So that a client can show how the store's contents hang together, the client can follow the links.

  Background:
    Given a store where a decision supersedes an older decision
    And two work items point at that decision
    And the older decision is tagged "pricing"

  @slice-30
  Scenario: The client follows the links out of an artifact
    Pins the simplest traversal: what an artifact points at comes back as stubs, enough to show without reading each target whole.
    When the client follows the links out of the decision
    Then the client is given a stub of the older decision

  @slice-30
  Scenario: The client follows the links into an artifact
    Pins that the store knows who points at a thing as well as what it points at, which is the question no single artifact can answer by itself.
    When the client follows the links into the decision
    Then the client is given a stub of each work item

  @slice-30
  Scenario: The client narrows the links to one link and one kind
    Pins that a traversal can be narrowed to one link and one kind, so a client asks its real question instead of filtering everything afterwards.
    When the client follows the links into the decision, only through the link a work item uses, and only from work items
    Then the client is given both work items and nothing else

  @slice-12
  Scenario: The client follows the links two steps out
    Pins that a traversal can go more than one step and reports the route to each thing found, so a client can explain why something turned up.
    When the client follows the links out of the decision two steps
    Then the client is given the older decision and the tag
    And each of them comes with the route taken to it
