# formulated from spec/capabilities/answer-a-damaged-file.md
Feature: Answer a damaged file
  Narrator: the client

  @slice-112.1
  Scenario Outline: A store whose database cannot be read, because it is damaged or missing beside its marker, refuses every call and command that needs it
    Pins that a database the store cannot read always gives the same named fault, naming the database, never a crash, with nothing written in the store or in a directory an export was aimed at.
    Given a store holding a decision, a process and a tag, each of a kind the store holds a type for
    And the store's database <damage>
    And an empty directory outside the store
    When the operator runs kb export in that store, aimed at the empty directory
    Then what was asked is rejected because the store's database cannot be read, and the database is named
    And the fault is given as any other fault is given, never breaking off
    And nothing is written in the store, nor in the empty directory, which stays as it was

    Examples:
      | damage                                              |
      | was damaged behind the store's back                 |
      | is missing, while the store's marker is still there |

  @slice-118
  Scenario Outline: A store whose database cannot be opened for writing, because the directory, the file or the mount it is on is read-only, refuses every call and command that needs it
    Pins that a store that cannot be written to gives the same named fault as a damaged one, naming the database, never a crash, with nothing written in the store or in a directory an export was aimed at.
    Given a store holding a decision, a process and a tag, each of a kind the store holds a type for
    And the store's database <where it is read-only>
    And an empty directory outside the store
    When the operator runs kb export in that store, aimed at the empty directory
    Then what was asked is rejected because the store's database cannot be read, and the database is named
    And the fault is given as any other fault is given, never breaking off
    And nothing is written in the store, nor in the empty directory, which stays as it was

    Examples:
      | where it is read-only                 |
      | lies in a directory that is read-only |
      | is a file that is read-only           |

  @slice-117
  Scenario Outline: A store found that was made by an earlier kb, in a form this kb cannot read, refuses every call and command that needs it
    Pins that an earlier kb's store always gives one named fault saying how to move it, however it is found, never a crash, with nothing written.
    Given a store holding a decision, a process and a tag, made by an earlier kb in a form this kb cannot read
    And the store is found <how the store is found>
    When the client creates a decision with a title and both required sections, saying which role and why
    Then what was asked is rejected because the store was made by an earlier version of kb
    And the fault says to start a new store and import the old one's files
    And the fault is given as any other fault is given, never breaking off
    And nothing is written in the store

    Examples:
      | how the store is found            |
      | upward from the working directory |
      | through KB_ROOT naming it         |

  @slice-118.3
  Scenario: A store found whose marker names a form of store this kb does not know, one a later kb made, refuses every call and command that needs it
    Pins that a later kb's store always gives one named fault saying a later version of kb is needed, never a crash, with the store not opened and nothing written.
    Given a store holding a decision, a process and a tag, whose marker names a form of store this kb does not know, one a later kb made
    When the client creates a decision with a title and both required sections, saying which role and why
    Then what was asked is rejected because the store was made by a later version of kb, which is needed to read it
    And the fault is given as any other fault is given, never breaking off
    And the store is not opened
    And nothing is written in the store

  @slice-118.3
  Scenario: A store found whose marker cannot be read at all refuses every call and command that needs it, as for a later kb's store
    Pins that a marker that cannot be read is answered as a later kb's store is, with one named fault, never a crash, and nothing written.
    Given a store holding a decision, a process and a tag, whose marker cannot be read at all
    When the client creates a decision with a title and both required sections, saying which role and why
    Then what was asked is rejected because the store was made by a later version of kb, which is needed to read it
    And the fault is given as any other fault is given, never breaking off
    And nothing is written in the store
