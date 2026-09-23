Feature: Add an item to a collection
So that a client can grow a collection an item at a time without rewriting the artifact, the client can add an item to a collection.

  Background:
    Given a store holding a process with two steps and a shared step other processes use

  @slice-65
  Scenario: The client adds an item to a collection
    When the client adds a step to the process, saying which role and why
    Then the client is given the new item's name and the artifact's new version
    And the new item comes after the items already there

  @slice-66
  Scenario: An item that uses another artifact keeps its settings on itself
    When the client adds a step that points at the shared step together with its settings, saying which role and why
    Then the settings are held by the new item
    And the shared step is unchanged
