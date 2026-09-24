Feature: Add an item to a collection
So that a client can grow a collection an item at a time without rewriting the artifact, the client can add an item to a collection.

  Background:
    Given a store holding a process with two steps and a shared step other processes use

  @slice-38
  Scenario: The client adds an item to a collection
    When the client adds a step to the process, saying which role and why
    Then the client is given the new item's name and the artifact's new version
    And the new item comes after the items already there

  @slice-38
  Scenario: The name of a new item comes from its title
    When the client adds a step titled "Count what is on the shelf" to the process, saying which role and why
    Then the name the client is given for the new item is made from that title
    And the client never said what the name should be

  @slice-38
  Scenario: An item of a kind that carries no title is named by its place
    Given an artifact holding a collection whose items carry no title of their own
    When the client adds an item to that collection, saying which role and why
    Then the name the client is given for the new item is made from its place in the collection

  @slice-38
  Scenario: A second item with a title already used in the collection gets a name of its own
    When the client adds a step whose title is already used by a step of that process, saying which role and why
    Then the name the client is given for the new item is the name already taken with a number added
    And the step already there keeps the name it had

  @slice-38
  Scenario: Taking an item out does not rename the items left
    Given an artifact holding a collection whose items carry no title of their own, each named by its place when it was added
    When the client takes the first item out of that collection, saying which role and why
    Then every item left keeps the name it was given when it was added
    And no item is named again from where it now sits

  @slice-49
  Scenario: Putting items in a different order does not rename them
    Given an artifact holding a collection whose items carry no title of their own, each named by its place when it was added
    When the client puts the items of that collection in a different order, saying which role and why
    Then every item keeps the name it was given when it was added
    And anything pointing at one of them still lands on the same item

  @slice-38
  Scenario: An item that uses another artifact keeps its settings on itself
    When the client adds a step that points at the shared step together with its settings, saying which role and why
    Then the settings are held by the new item
    And the shared step is unchanged

  Scenario: An item whose content settles what only the store settles is refused
    When the client adds a step whose content carries a name of its own, saying which role and why
    Then the item is rejected because content holds only what the type declares, and the thing it carried that only the store settles is named back
    And the process holds the steps it held before, at the version it held before

  Scenario: Adding an item to something the store does not hold is refused
    When the client adds a step to a process by a name the store holds nothing under, saying which role and why
    Then the item is rejected because the store holds nothing by that name, and the name asked for is given back
    And nothing is written anywhere in the store
