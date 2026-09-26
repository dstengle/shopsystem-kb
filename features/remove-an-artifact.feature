Feature: Remove an artifact
So that a client can take out what is no longer used without leaving links pointing at nothing, the client can remove an artifact.

  Background:
    Given a store holding a tag nothing points at
    And a tag a decision points at

  @slice-41
  Scenario: The client removes an artifact nothing points at
    Pins that removal is a change like any other, recorded in the history, and not a quiet disappearance.
    When the client removes the tag nothing points at, saying which role and why
    Then the store no longer holds it
    And the removal is recorded like any other change

  @slice-41
  Scenario: A removal something points at is refused
    Pins the only rule the store has for removals: refuse, and hand back every link in the way so the client can decide what to do about them.
    When the client removes the tag the decision points at, saying which role and why
    Then the removal is rejected because something still points at it
    And the client is given every link that blocks it

  @slice-41
  Scenario: Removing something the store does not hold is refused
    Pins that removing what is not there is an answer naming what was asked for, rather than a success that silently did nothing.
    When the client removes an artifact by a name the store holds nothing under, saying which role and why
    Then the removal is rejected because the store holds nothing by that name, and the name asked for is given back
    And the store holds what it held before

  @slice-87
  Scenario: A link from inside a part blocks a removal like any other
    Pins that a link is a link wherever it sits: one written inside an item of a collection holds back a removal too, so nothing is ever left pointing at nothing.
    Given a process one of whose steps points at the tag nothing else points at
    When the client removes that tag, saying which role and why
    Then the removal is rejected because something still points at it
    And the client is given that link among the links that block it

  @slice-87
  Scenario: A name is free again once what held it has been removed
    Pins that a name belongs to an artifact for its life and no longer, so the next artifact whose title gives that name simply takes it, at its own first version.
    Given the client has removed the tag nothing points at
    When the client creates a tag with the title the removed one had, saying which role and why
    Then the client is given the name the removed tag had, with no number added
    And the new tag is at its first version
