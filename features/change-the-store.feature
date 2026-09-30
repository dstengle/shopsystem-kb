# formulated from spec/capabilities/change-the-store.md
Feature: Change the store
  Narrator: the client

  @slice-1
  Scenario: The client creates an artifact
    Pins the walking skeleton's write: a create goes through checking to disk and comes back as a name the client can use, with the content reading back in the order the type declares.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision with a title, both required sections and two options, saying which role and why
    Then the client is given the name the artifact keeps for life and its first version
    And the artifact records the version of the type it was checked against
    And reading it back gives what was written, in the order the type declares

  @slice-1.6
  Scenario: An artifact created without a title is refused
    Pins that a title is not optional, because the store has nothing to make a name from without one.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision with both required sections and no title, saying which role and why
    Then the artifact is rejected because an artifact cannot be created without a title

  @slice-23
  Scenario: The client changes an artifact
    Pins what a successful write leaves behind: the version counts up by one and the artifact records which version of its type it was checked against.
    Given a store holding a decision with a purpose and a rationale, at its first version
    When the client replaces the decision, saying which role and why
    Then the version goes up by one
    And the artifact records the current version of its type

  @slice-13
  Scenario: The client changes one node inside an artifact
    Pins that a change can be aimed at a node inside an artifact, so a client can correct one section without resending everything around it.
    Given a store holding a decision with a purpose and a rationale, at its first version
    When the client replaces the rationale of the decision, saying which role and why
    Then only that section changes
    And the rest of the decision reads as before

  @slice-86
  Scenario: The client changes one item of a collection
    Pins that a change can be aimed at one item of a collection, and that the item keeps the name it was given, because a name is worked out once and never again.
    Given a store holding a decision with a purpose and a rationale, at its first version
    Given the decision carries two options
    When the client replaces one of the options, saying which role and why
    Then only that option changes
    And it keeps the name it was given when it was created
    And anything pointing at it still lands on it

  @slice-39
  Scenario: The client adds an item to a collection
    Pins adding as an operation of its own: one item goes in without resending the artifact, and what comes back is a name for that item plus the artifact's new version.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step to the process, saying which role and why
    Then the client is given the new item's name and the artifact's new version
    And the new item comes after the items already there

  @slice-39
  Scenario: An item that uses another artifact keeps its settings on itself
    Pins where state belonging to a use lives: on the item doing the using, never on the shared thing, so one use's settings cannot leak into another's.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step that points at the shared step together with its settings, saying which role and why
    Then the settings are held by the new item
    And the shared step is unchanged

  @slice-77
  Scenario: The client adds an item to a collection inside an item
    Pins that a collection inside an item is a collection like any other, named by the item it sits in, so growing one does not mean rewriting the whole artifact.
    Given a store holding a process with two steps and a shared step other processes use
    Given the steps of the process each carry a collection of checks of their own
    When the client adds a check to the first step of the process, saying which role and why
    Then the client is given the new check's name and the artifact's new version
    And the rest of the process is unchanged

  @slice-41
  Scenario: The client removes an artifact nothing points at
    Pins that removal is a change like any other, recorded in the history, and not a quiet disappearance.
    Given a store holding a tag nothing points at
    And a tag a decision points at
    When the client removes the tag nothing points at, saying which role and why
    Then the store no longer holds it
    And the removal is recorded like any other change

  @slice-41
  Scenario: A removal something points at is refused
    Pins the only rule the store has for removals: refuse, and hand back every link in the way so the client can decide what to do about them.
    Given a store holding a tag nothing points at
    And a tag a decision points at
    When the client removes the tag the decision points at, saying which role and why
    Then the removal is rejected because something still points at it
    And the client is given every link that blocks it

  @slice-87
  Scenario: A link from inside a part blocks a removal like any other
    Pins that a link is a link wherever it sits: one written inside an item of a collection holds back a removal too, so nothing is ever left pointing at nothing.
    Given a store holding a tag nothing points at
    And a tag a decision points at
    Given a process one of whose steps points at the tag nothing else points at
    When the client removes that tag, saying which role and why
    Then the removal is rejected because something still points at it
    And the client is given that link among the links that block it
