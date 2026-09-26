Feature: A file in the store that cannot be read
So that damage done to the store behind its back never reaches a client as a crash, every call answers a file it cannot read with a named fault.

  Background:
    Given a store holding a decision, a process and a tag, each of a kind the store holds a type for

  @slice-74
  Scenario Outline: Every shape of damage to a stored file is the one named finding
    Pins that "cannot be read" means every way a file can stop making sense, not only a mangled bracket, so no shape of damage reaches a client as a crash.
    Given someone edited the decision's file by hand and left it <damage>
    When the client checks the store
    Then that file is reported as a violation, naming the file
    And everything else in the store is checked and reported alongside it
    And the check comes back with its answer rather than breaking off

    Examples:
      | damage                                                |
      | in a shape that cannot be read at all                 |
      | empty, with nothing in it                             |
      | holding a list rather than a set of named entries     |
      | holding a second document after the first             |
      | telling a reader how to build one of its values       |
      | pointing back at a value written elsewhere in it      |
      | naming the same entry twice                           |

  @slice-63
  Scenario Outline: Every call refuses a file it cannot read, naming the file
    Pins that the fault is the same answer whichever call runs into the damage, so no client has to handle one call breaking off where another answers politely.
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
    Given someone edited the decision type's file by hand and left it in a shape the store cannot read
    When the client creates a decision with a title and both required sections, saying which role and why
    Then the create is rejected because that file cannot be read, and the file is named
    And nothing is written anywhere in the store

  @slice-79
  Scenario: An entry of the history that cannot be read is refused in the same way
    Pins that the history is held to the same rule as the content, so a damaged entry is a named fault rather than a crash in the middle of reading the past.
    Given someone edited one of the store's history entries by hand and left it in a shape the store cannot read
    When the client reads the journal
    Then the read is rejected because that file cannot be read, and the file is named
    And the client is given that fault as it is given any other, the call never breaking off
