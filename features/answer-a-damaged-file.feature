# formulated from spec/capabilities/answer-a-damaged-file.md
Feature: Answer a damaged file
  Narrator: the client

  Scenario Outline: A store whose database cannot be read, because it is damaged or missing beside its marker, refuses every call and command that needs it
    Pins that a database the store cannot read always gives the same named fault, naming the database, never a crash, with nothing served and nothing written in the store or in a directory an export was aimed at.
    Given a store holding a decision, a process and a tag, each of a kind the store holds a type for
    And the store's database <damage>
    And an empty directory outside the store
    When <someone does something that needs the store>
    Then what was asked is rejected because the store's database cannot be read, and the database is named
    And the fault is given as any other fault is given, never breaking off
    And nothing is served
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
      | was damaged behind the store's back                 | the operator runs kb serve in that store                                                                         |
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
      | is missing, while the store's marker is still there | the operator runs kb serve in that store                                                                         |
      | is missing, while the store's marker is still there | the operator runs kb export in that store, aimed at the empty directory                                          |
      | is missing, while the store's marker is still there | the operator checks a directory exported from another store for import in that store                             |
      | is missing, while the store's marker is still there | the operator runs kb import in that store on a directory exported from another store, saying which role they are |
