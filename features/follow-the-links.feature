Feature: Follow the links
So that a client can show how the store's contents hang together, the client can follow the links.

  Background:
    Given a store where a decision supersedes an older decision
    And two work items point at that decision
    And the older decision is tagged "pricing"

  @assumes-typed-refs-cover-the-questions
  Scenario: The client follows the links out of an artifact
    When the client follows the links out of the decision
    Then the client is given a stub of the older decision

  @assumes-typed-refs-cover-the-questions
  Scenario: The client follows the links into an artifact
    When the client follows the links into the decision
    Then the client is given a stub of each work item

  @assumes-typed-refs-cover-the-questions
  Scenario: The client narrows the links to one link and one kind
    When the client follows the links into the decision, only through the link a work item uses, and only from work items
    Then the client is given both work items and nothing else

  @assumes-typed-refs-cover-the-questions
  Scenario: The client follows the links two steps out
    When the client follows the links out of the decision two steps
    Then the client is given the older decision and the tag
    And each of them comes with the route taken to it
