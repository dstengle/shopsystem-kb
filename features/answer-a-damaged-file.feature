# formulated from spec/capabilities/answer-a-damaged-file.md
Feature: Answer a damaged file
  Narrator: the client

  @slice-1.19
  Scenario: Reading an artifact whose stored file cannot be read is refused
    Pins that damage done behind the store's back surfaces as an ordinary named fault, so one broken file cannot take a client down.
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    Given someone edited the decision's file by hand and left it in a shape the store cannot read
    When the client reads the decision
    Then the read is rejected because that file cannot be read, and the file is named
    And the client is given that fault as it is given any other, the call never breaking off

  @slice-63
  Scenario Outline: Every call refuses a file it cannot read, naming the file
    Pins that the fault is the same answer whichever call runs into the damage, so no client has to handle one call breaking off where another answers politely.
    Given a store holding a decision, a process and a tag, each of a kind the store holds a type for
    Given someone edited the decision's file by hand and left it in a shape the store cannot read
    When the client <call>
    Then the call is rejected because that file cannot be read, and the file is named
    And the client is given that fault as it is given any other, the call never breaking off
    And nothing is written anywhere in the store

    Examples:
      | call                                                        |
      | replaces the decision, saying which role and why            |
      | adds an item to a collection of the decision, saying which role and why |
      | removes the decision, saying which role and why             |
      | lists the decisions                                         |
      | searches the prose for a word that decision holds           |
      | follows the links into the decision                         |
      | follows the links out of the decision                       |

  @slice-79
  Scenario: Creating an artifact of a kind whose type cannot be read is refused
    Pins that a type the store cannot read is the same named fault as any other damaged file, rather than a crash in the middle of checking a perfectly good artifact against it.
    Given a store holding a decision, a process and a tag, each of a kind the store holds a type for
    Given someone edited the decision type's file by hand and left it in a shape the store cannot read
    When the client creates a decision with a title and both required sections, saying which role and why
    Then the create is rejected because that file cannot be read, and the file is named
    And nothing is written anywhere in the store

  @slice-79
  Scenario: An entry of the history that cannot be read is refused in the same way
    Pins that the history is held to the same rule as the content, so a damaged entry is a named fault rather than a crash in the middle of reading the past.
    Given a store holding a decision, a process and a tag, each of a kind the store holds a type for
    Given someone edited one of the store's history entries by hand and left it in a shape the store cannot read
    When the client reads the journal
    Then the read is rejected because that file cannot be read, and the file is named
    And the client is given that fault as it is given any other, the call never breaking off
