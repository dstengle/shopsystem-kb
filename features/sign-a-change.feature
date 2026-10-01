# formulated from spec/capabilities/sign-a-change.md
Feature: Sign a change
  Narrator: the client

  Background:
    Given a store holding a decision with a purpose and a rationale, at its first version

  @slice-96
  Scenario Outline: A change that does not say which role made it, or why, is refused
    Pins that every change is attributable before anything is written: whichever call makes it, a change missing its role or its reason leaves nothing on disk to be read and nothing in the history.
    Given the decision carries two options
    When the client <call>, <saying>
    Then the change is rejected because <reason>
    And reading the decision gives what it held before, at the version it held before
    And the store holds no artifact it did not hold before
    And the store's history holds no entry for it

    Examples:
      | call                                                                                | saying                                                            | reason                                                 |
      | creates another decision                                                            | saying why but not which role it is                               | every entry in the history names the role that made it |
      | creates another decision                                                            | saying which role it is but not why                               | every entry in the history says why it was made        |
      | replaces the decision                                                               | saying why but not which role it is                               | every entry in the history names the role that made it |
      | replaces the decision                                                               | saying which role it is but not why                               | every entry in the history says why it was made        |
      | adds an option to the decision                                                      | saying why but not which role it is                               | every entry in the history names the role that made it |
      | adds an option to the decision                                                      | saying which role it is but not why                               | every entry in the history says why it was made        |
      | removes the decision                                                                | saying why but not which role it is                               | every entry in the history names the role that made it |
      | removes the decision                                                                | saying which role it is but not why                               | every entry in the history says why it was made        |
      | asks, in one go, for two other decisions to be created                           | saying why but not which role it is                               | every entry in the history names the role that made it |
      | asks, in one go, for two other decisions to be created                           | saying which role it is but not why                               | every entry in the history says why it was made        |
      | creates another decision                                                            | saying why but giving a role that is only blank space             | every entry in the history names the role that made it |
      | creates another decision                                                            | saying which role it is but giving as its reason only blank space | every entry in the history says why it was made        |
      | replaces the decision                                                               | saying why but giving a role that is only blank space             | every entry in the history names the role that made it |
      | replaces the decision                                                               | saying which role it is but giving as its reason only blank space | every entry in the history says why it was made        |
      | adds an option to the decision                                                      | saying why but giving a role that is only blank space             | every entry in the history names the role that made it |
      | adds an option to the decision                                                      | saying which role it is but giving as its reason only blank space | every entry in the history says why it was made        |
      | removes the decision                                                                | saying why but giving a role that is only blank space             | every entry in the history names the role that made it |
      | removes the decision                                                                | saying which role it is but giving as its reason only blank space | every entry in the history says why it was made        |
      | asks, in one go, for two other decisions to be created                           | saying why but giving a role that is only blank space             | every entry in the history names the role that made it |
      | asks, in one go, for two other decisions to be created                           | saying which role it is but giving as its reason only blank space | every entry in the history says why it was made        |
