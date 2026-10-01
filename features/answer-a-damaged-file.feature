# formulated from spec/capabilities/answer-a-damaged-file.md
Feature: Answer a damaged file
  Narrator: the client

  @slice-112.1
  Scenario Outline: A store whose database cannot be read, because it is damaged or missing beside its marker, refuses every call and command that needs it
    Pins that a database the store cannot read always gives the same named fault, naming the database, never a crash, with nothing written in the store or in a directory an export was aimed at.
    Given a store holding a decision, a process and a tag, each of a kind the store holds a type for
    And the store's database <damage>
    And an empty directory outside the store
    When <someone does something that needs the store>
    Then what was asked is rejected because the store's database cannot be read, and the database is named
    And the fault is given as any other fault is given, never breaking off
    And nothing is written in the store, nor in the empty directory, which stays as it was

    Examples:
      | damage                                              | someone does something that needs the store                                                                      |
      | was damaged behind the store's back                 | the client creates a decision with a title and both required sections, saying which role and why                 |
      | was damaged behind the store's back                 | the client reads the decision                                                                                    |
      | was damaged behind the store's back                 | the client replaces the decision, saying which role and why                                                      |
      | was damaged behind the store's back                 | the client adds an item to a collection of the decision, saying which role and why                               |
      | was damaged behind the store's back                 | the client removes the decision, saying which role and why                                                       |
      | was damaged behind the store's back                 | the client asks, in one go, for two decisions to be created, saying which role and why                           |
      | was damaged behind the store's back                 | the client lists the decisions                                                                                   |
      | was damaged behind the store's back                 | the client follows the links out of the decision                                                                 |
      | was damaged behind the store's back                 | the client follows the links into the decision                                                                   |
      | was damaged behind the store's back                 | the client searches the prose for a word that decision holds                                                     |
      | was damaged behind the store's back                 | the client reads the journal                                                                                     |
      | was damaged behind the store's back                 | the client snapshots the decision and the process for a piece of work                                            |
      | was damaged behind the store's back                 | the client checks the store                                                                                      |
      | was damaged behind the store's back                 | the operator runs kb validate in that store                                                                      |
      | was damaged behind the store's back                 | the operator runs kb export in that store, aimed at the empty directory                                          |
      | was damaged behind the store's back                 | the operator checks a directory exported from another store for import in that store                             |
      | was damaged behind the store's back                 | the operator runs kb import in that store on a directory exported from another store, saying which role they are |
      | is missing, while the store's marker is still there | the client creates a decision with a title and both required sections, saying which role and why                 |
      | is missing, while the store's marker is still there | the client reads the decision                                                                                    |
      | is missing, while the store's marker is still there | the client replaces the decision, saying which role and why                                                      |
      | is missing, while the store's marker is still there | the client adds an item to a collection of the decision, saying which role and why                               |
      | is missing, while the store's marker is still there | the client removes the decision, saying which role and why                                                       |
      | is missing, while the store's marker is still there | the client asks, in one go, for two decisions to be created, saying which role and why                           |
      | is missing, while the store's marker is still there | the client lists the decisions                                                                                   |
      | is missing, while the store's marker is still there | the client follows the links out of the decision                                                                 |
      | is missing, while the store's marker is still there | the client follows the links into the decision                                                                   |
      | is missing, while the store's marker is still there | the client searches the prose for a word that decision holds                                                     |
      | is missing, while the store's marker is still there | the client reads the journal                                                                                     |
      | is missing, while the store's marker is still there | the client snapshots the decision and the process for a piece of work                                            |
      | is missing, while the store's marker is still there | the client checks the store                                                                                      |
      | is missing, while the store's marker is still there | the operator runs kb validate in that store                                                                      |
      | is missing, while the store's marker is still there | the operator runs kb export in that store, aimed at the empty directory                                          |
      | is missing, while the store's marker is still there | the operator checks a directory exported from another store for import in that store                             |
      | is missing, while the store's marker is still there | the operator runs kb import in that store on a directory exported from another store, saying which role they are |

  Scenario Outline: A store whose database cannot be opened for writing, because the directory, the file or the mount it is on is read-only, refuses every call and command that needs it
    Pins that a store that cannot be written to gives the same named fault as a damaged one, naming the database, never a crash, with nothing written in the store or in a directory an export was aimed at.
    Given a store holding a decision, a process and a tag, each of a kind the store holds a type for
    And the store's database <where it is read-only>
    And an empty directory outside the store
    When <someone does something that needs the store>
    Then what was asked is rejected because the store's database cannot be read, and the database is named
    And the fault is given as any other fault is given, never breaking off
    And nothing is written in the store, nor in the empty directory, which stays as it was

    Examples:
      | where it is read-only                 | someone does something that needs the store                                                                      |
      | lies in a directory that is read-only | the client creates a decision with a title and both required sections, saying which role and why                 |
      | lies in a directory that is read-only | the client reads the decision                                                                                    |
      | lies in a directory that is read-only | the client replaces the decision, saying which role and why                                                      |
      | lies in a directory that is read-only | the client adds an item to a collection of the decision, saying which role and why                               |
      | lies in a directory that is read-only | the client removes the decision, saying which role and why                                                       |
      | lies in a directory that is read-only | the client asks, in one go, for two decisions to be created, saying which role and why                           |
      | lies in a directory that is read-only | the client lists the decisions                                                                                   |
      | lies in a directory that is read-only | the client follows the links out of the decision                                                                 |
      | lies in a directory that is read-only | the client follows the links into the decision                                                                   |
      | lies in a directory that is read-only | the client searches the prose for a word that decision holds                                                     |
      | lies in a directory that is read-only | the client reads the journal                                                                                     |
      | lies in a directory that is read-only | the client snapshots the decision and the process for a piece of work                                            |
      | lies in a directory that is read-only | the client checks the store                                                                                      |
      | lies in a directory that is read-only | the operator runs kb validate in that store                                                                      |
      | lies in a directory that is read-only | the operator runs kb export in that store, aimed at the empty directory                                          |
      | lies in a directory that is read-only | the operator checks a directory exported from another store for import in that store                             |
      | lies in a directory that is read-only | the operator runs kb import in that store on a directory exported from another store, saying which role they are |
      | is a file that is read-only           | the client creates a decision with a title and both required sections, saying which role and why                 |
      | is a file that is read-only           | the client reads the decision                                                                                    |
      | is a file that is read-only           | the client replaces the decision, saying which role and why                                                      |
      | is a file that is read-only           | the client adds an item to a collection of the decision, saying which role and why                               |
      | is a file that is read-only           | the client removes the decision, saying which role and why                                                       |
      | is a file that is read-only           | the client asks, in one go, for two decisions to be created, saying which role and why                           |
      | is a file that is read-only           | the client lists the decisions                                                                                   |
      | is a file that is read-only           | the client follows the links out of the decision                                                                 |
      | is a file that is read-only           | the client follows the links into the decision                                                                   |
      | is a file that is read-only           | the client searches the prose for a word that decision holds                                                     |
      | is a file that is read-only           | the client reads the journal                                                                                     |
      | is a file that is read-only           | the client snapshots the decision and the process for a piece of work                                            |
      | is a file that is read-only           | the client checks the store                                                                                      |
      | is a file that is read-only           | the operator runs kb validate in that store                                                                      |
      | is a file that is read-only           | the operator runs kb export in that store, aimed at the empty directory                                          |
      | is a file that is read-only           | the operator checks a directory exported from another store for import in that store                             |
      | is a file that is read-only           | the operator runs kb import in that store on a directory exported from another store, saying which role they are |

  Scenario Outline: A store found that was made by an earlier kb, in a form this kb cannot read, refuses every call and command that needs it
    Pins that an earlier kb's store always gives one named fault saying how to move it, however it is found, never a crash, with nothing written.
    Given a store holding a decision, a process and a tag, made by an earlier kb in a form this kb cannot read
    And the store is found <how the store is found>
    And an empty directory outside the store
    When <someone does something that needs the store>
    Then what was asked is rejected because the store was made by an earlier version of kb
    And the fault says to start a new store and import the old one's files
    And the fault is given as any other fault is given, never breaking off
    And nothing is written in the store, nor in the empty directory, which stays as it was

    Examples:
      | how the store is found            | someone does something that needs the store                                                                      |
      | upward from the working directory | the client creates a decision with a title and both required sections, saying which role and why                 |
      | upward from the working directory | the client reads the decision                                                                                    |
      | upward from the working directory | the client replaces the decision, saying which role and why                                                      |
      | upward from the working directory | the client adds an item to a collection of the decision, saying which role and why                               |
      | upward from the working directory | the client removes the decision, saying which role and why                                                       |
      | upward from the working directory | the client asks, in one go, for two decisions to be created, saying which role and why                           |
      | upward from the working directory | the client lists the decisions                                                                                   |
      | upward from the working directory | the client follows the links out of the decision                                                                 |
      | upward from the working directory | the client follows the links into the decision                                                                   |
      | upward from the working directory | the client searches the prose for a word that decision holds                                                     |
      | upward from the working directory | the client reads the journal                                                                                     |
      | upward from the working directory | the client snapshots the decision and the process for a piece of work                                            |
      | upward from the working directory | the client checks the store                                                                                      |
      | upward from the working directory | the operator runs kb validate in that store                                                                      |
      | upward from the working directory | the operator runs kb export in that store, aimed at the empty directory                                          |
      | upward from the working directory | the operator checks a directory exported from another store for import in that store                             |
      | upward from the working directory | the operator runs kb import in that store on a directory exported from another store, saying which role they are |
      | through KB_ROOT naming it         | the client creates a decision with a title and both required sections, saying which role and why                 |
      | through KB_ROOT naming it         | the client reads the decision                                                                                    |
      | through KB_ROOT naming it         | the client replaces the decision, saying which role and why                                                      |
      | through KB_ROOT naming it         | the client adds an item to a collection of the decision, saying which role and why                               |
      | through KB_ROOT naming it         | the client removes the decision, saying which role and why                                                       |
      | through KB_ROOT naming it         | the client asks, in one go, for two decisions to be created, saying which role and why                           |
      | through KB_ROOT naming it         | the client lists the decisions                                                                                   |
      | through KB_ROOT naming it         | the client follows the links out of the decision                                                                 |
      | through KB_ROOT naming it         | the client follows the links into the decision                                                                   |
      | through KB_ROOT naming it         | the client searches the prose for a word that decision holds                                                     |
      | through KB_ROOT naming it         | the client reads the journal                                                                                     |
      | through KB_ROOT naming it         | the client snapshots the decision and the process for a piece of work                                            |
      | through KB_ROOT naming it         | the client checks the store                                                                                      |
      | through KB_ROOT naming it         | the operator runs kb validate in that store                                                                      |
      | through KB_ROOT naming it         | the operator runs kb export in that store, aimed at the empty directory                                          |
      | through KB_ROOT naming it         | the operator checks a directory exported from another store for import in that store                             |
      | through KB_ROOT naming it         | the operator runs kb import in that store on a directory exported from another store, saying which role they are |
