Feature: Add an item to a collection
So that a client can grow a collection an item at a time without rewriting the artifact, the client can add an item to a collection.

  Background:
    Given a store holding a process with two steps and a shared step other processes use

  @slice-39
  Scenario: The client adds an item to a collection
    Pins adding as an operation of its own: one item goes in without resending the artifact, and what comes back is a name for that item plus the artifact's new version.
    When the client adds a step to the process, saying which role and why
    Then the client is given the new item's name and the artifact's new version
    And the new item comes after the items already there

  @slice-39
  Scenario: The name of a new item comes from its title
    Pins that the store mints an item's name from the item's own title, so a client never chooses names and two clients cannot disagree about them.
    When the client adds a step titled "Count what is on the shelf" to the process, saying which role and why
    Then the name the client is given for the new item is made from that title
    And the client never said what the name should be

  @slice-39
  Scenario: An item of a kind that carries no title is named by its place
    Pins the fallback for collections whose items have no title: the store still mints a name, from where the item went in, so every item is addressable.
    Given an artifact holding a collection whose items carry no title of their own
    When the client adds an item to that collection, saying which role and why
    Then the name the client is given for the new item is made from its place in the collection

  @slice-39
  Scenario: A second item with a title already used in the collection gets a name of its own
    Pins that names are unique within a collection: a clash is settled by adding a number, and the item already there is never renamed under anything pointing at it.
    When the client adds a step whose title is already used by a step of that process, saying which role and why
    Then the name the client is given for the new item is the name already taken with a number added
    And the step already there keeps the name it had

  @slice-39
  Scenario: Taking an item out does not rename the items left
    Pins that a name is minted once and never worked out again, so removing an item cannot quietly move every later item's name out from under a link.
    Given an artifact holding a collection whose items carry no title of their own, each named by its place when it was added
    When the client takes the first item out of that collection, saying which role and why
    Then every item left keeps the name it was given when it was added
    And no item is named again from where it now sits

  @slice-14
  Scenario: Putting items in a different order does not rename them
    Pins the same for reordering: order is content, names are identity, and rearranging a collection leaves every link landing where it did.
    Given an artifact holding a collection whose items carry no title of their own, each named by its place when it was added
    When the client puts the items of that collection in a different order, saying which role and why
    Then every item keeps the name it was given when it was added
    And anything pointing at one of them still lands on the same item

  @slice-39
  Scenario: An item that uses another artifact keeps its settings on itself
    Pins where state belonging to a use lives: on the item doing the using, never on the shared thing, so one use's settings cannot leak into another's.
    When the client adds a step that points at the shared step together with its settings, saying which role and why
    Then the settings are held by the new item
    And the shared step is unchanged

  @slice-39
  Scenario: An item whose content settles what only the store settles is refused
    Pins that content carries only what the type declares here too: an item cannot smuggle in its own identity, and the refusal leaves the collection as it was.
    When the client adds a step whose content carries a name of its own, saying which role and why
    Then the item is rejected because content holds only what the type declares, and the thing it carried that only the store settles is named back
    And the process holds the steps it held before, at the version it held before

  @slice-39
  Scenario: Adding an item to something the store does not hold is refused
    Pins that a missing artifact is an ordinary answer naming the name asked for, not a crash, and that the refused add writes nothing.
    When the client adds a step to a process by a name the store holds nothing under, saying which role and why
    Then the item is rejected because the store holds nothing by that name, and the name asked for is given back
    And nothing is written anywhere in the store
