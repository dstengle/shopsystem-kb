Feature: Add an item to a collection
So that a client can grow a collection an item at a time without rewriting the artifact, the client can add an item to a collection.

  Background:
    Given a store holding a process with two steps and a shared step other processes use

  @slice-38
  Scenario: The client adds an item to a collection
    When the client adds a step to the process, saying which role and why
    Then the client is given the new item's name and the artifact's new version
    And the new item comes after the items already there

  Scenario: The name of a new item comes from its title
    When the client adds a step titled "Count what is on the shelf" to the process, saying which role and why
    Then the name the client is given for the new item is made from that title
    And the client never said what the name should be

  Scenario: An item of a kind that carries no title is named by its place
    Given an artifact holding a collection whose items carry no title of their own
    When the client adds an item to that collection, saying which role and why
    Then the name the client is given for the new item is made from its place in the collection

  Scenario: A second item with a title already used in the collection gets a name of its own
    When the client adds a step whose title is already used by a step of that process, saying which role and why
    Then the name the client is given for the new item is the name already taken with a number added
    And the step already there keeps the name it had

  @slice-38
  Scenario: An item that uses another artifact keeps its settings on itself
    When the client adds a step that points at the shared step together with its settings, saying which role and why
    Then the settings are held by the new item
    And the shared step is unchanged
