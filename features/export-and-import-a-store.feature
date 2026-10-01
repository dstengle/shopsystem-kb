# formulated from spec/capabilities/export-and-import-a-store.md
Feature: Export and import a store
  Narrator: the operator

  Scenario Outline: The operator exports the store to a directory that is empty or does not exist
    Pins what an export is: one readable file per artifact, kept by kind with types in their own place, saying who the artifact is before what it holds, all taken from a single moment of the store.
    Given a store holding a type for decisions, a type for work items, two decisions and a work item
    And a directory for the export that <state>
    When the operator exports the store to that directory
    Then the directory holds one file for each artifact in the store, under a folder named for its kind
    And the types' files are under the folder for types
    And each file gives the artifact's identity first, its name, kind, type version, revision and title, and then its content
    And every file shows the store as it stood at one moment

    Examples:
      | state           |
      | is empty        |
      | does not exist  |

  Scenario: The operator opens an exported artifact's file
    Pins that the exported files are meant to be read and reviewed by people: prose in blocks, lists under their names, no rewrapping, and nothing in them that instructs a reader how to build a value.
    Given a store holding a decision whose purpose is one short line and which carries a list of options, exported to a directory
    When the operator opens the decision's exported file
    Then every piece of prose stands as a block of its own, however short it is
    And each list is written beneath the name it belongs to, indented under it
    And no line of prose has been broken to fit a width
    And nothing in the file tells a reader how to build a value

  Scenario: Two stores given the same content by the same client are exported
    Pins that exporting is deterministic, which is what makes a difference between two exports mean a real change rather than a reshuffle.
    Given two stores each given the same decision by the same client, and each exported to a directory of its own
    When the operator compares the two exported decision files
    Then the two files are the same, byte for byte

  Scenario: Exporting to a directory that holds anything is refused
    Pins that an export never writes over what is already there.
    Given a store holding a decision
    And a directory that already holds a file
    When the operator exports the store to that directory
    Then the export is rejected because export never overwrites
    And what the directory holds is left as it was

  Scenario Outline: The operator checks a directory for import and each error is reported by file and reason
    Pins that the check reads every file rather than stopping at the first fault, and that each fault names the file it is in and the reason it is one.
    Given a store
    And a directory for import holding well-formed files and two files that each <fault>
    When the operator checks the directory for import
    Then each of the two files is reported as an error, naming the file, with the reason that <reason>

    Examples:
      | fault                                                               | reason                                                                |
      | cannot be read as YAML 1.2                                          | it cannot be read as YAML 1.2                                         |
      | is not in canonical form                                            | it is not in canonical form                                           |
      | claims a kind neither the directory nor the store holds a type for  | it claims a kind neither the directory nor the store holds a type for |
      | has content that does not fit its type                              | its content does not fit its type                                     |
      | carries a link that lands on nothing in the directory or the store  | it carries a link that lands on nothing in the directory or the store |

  Scenario Outline: The operator checks a directory for import that holds a file with an error, and files link to it
    Pins that a broken file's reach is shown: every file that leads to it by links, however indirectly, an artifact's link to its own type counting as one, is named as one that would be skipped, with the way it leads there.
    Given a store
    And a directory for import holding <broken>, and <linking>
    When the operator checks the directory for import
    Then <skipped> reported as a file that would be skipped, each with the chain of links that leads from it to the broken file

    Examples:
      | broken                                                                         | linking                                                                                   | skipped                                |
      | a file with an error                                                           | a file that links to the broken file directly                                             | the file that links to it is           |
      | a file with an error                                                           | a file that links to a second file, which links to the broken file                        | the second file and the first file are |
      | a type for decisions whose content does not fit the type that describes types  | a decision, whose link to its own type leads to the broken file                           | the decision is                        |
      | a type for decisions whose content does not fit the type that describes types  | a work item that links to a decision, whose link to its own type leads to the broken file | the decision and the work item are     |

  Scenario: The operator checks a directory for import that holds no error
    Pins that a clean directory is said to be clean.
    Given a store
    And a directory for import in which every file is well formed, fits its type and links only to what is there
    When the operator checks the directory for import
    Then the check reports success

  Scenario: A directory checked for import holds an error
    Pins that any error at all makes the check fail, so a directory with one is never taken as fit to import.
    Given a store
    And a directory for import holding one file whose content does not fit its type
    When the operator checks the directory for import
    Then the check reports failure

  Scenario: The operator imports a directory that checks clean into a freshly started store, saying which role they are
    Pins that an import lands whole as one signed change, saying where it came from, and that each artifact arrives as it was rather than as something new.
    Given a freshly started store
    And a directory for import that checks clean, holding a type for decisions and a decision at revision 3 written against version 2 of the decision type
    When the operator imports the directory, saying which role they are
    Then everything in the directory lands as one set, signed by that role, with a message naming the directory
    And the decision lands under the same name and title, at revision 3, written against version 2 of the decision type
    And the type for decisions lands under the same name and title, at the revision and type version the directory gives it

  Scenario: The operator imports a directory that checks clean, and the history shows each type landing before its artifacts
    Pins the order an import lands in and what it leaves in the history: the store's start, then one import entry per artifact, a type always ahead of the artifacts of its kind.
    Given a freshly started store
    And a directory for import that checks clean, holding a type for decisions, a type for work items, two decisions and a work item
    When the operator imports the directory, saying which role they are
    Then the store's history holds its starting entry followed by one import entry for each of the five artifacts, and nothing else
    And in the history each type's import entry comes before the import entries of the artifacts of its kind

  Scenario: Importing a directory that holds an error is refused
    Pins that import always checks first and takes nothing from a directory whose check fails, showing the operator why.
    Given a freshly started store
    And a directory for import holding one file whose content does not fit its type
    When the operator imports the directory, saying which role they are
    Then the import is rejected because the check found errors
    And the operator is shown the check's report
    And nothing is written

  Scenario Outline: The operator imports with errors skipped
    Pins that skipping errors leaves out exactly the broken files and everything that leads to them, a broken type taking the artifacts of its kind with it, lands the rest, and says what was left out and why.
    Given a freshly started store
    And a directory for import holding a type for work items and a work item that leads to no broken file, together with <broken>
    When the operator imports the directory with errors skipped, saying which role they are
    Then the type for work items and the work item land
    And <left out> do not land
    And the operator is told what was skipped and why

    Examples:
      | broken                                                                                                             | left out                                                     |
      | a type for decisions, a decision with an error and a decision that links to it                                     | the decision with an error and the decision that links to it |
      | a type for decisions, a decision with an error, a decision that links to it, and a decision that links to that one | the three decisions                                          |
      | a type for decisions whose content does not fit the type that describes types, and a decision                      | the type for decisions and the decision                      |

  Scenario: Importing into a store that holds an artifact besides the type that describes types is refused
    Pins that import never merges: it only fills a store that holds nothing yet.
    Given a store that has been given a type for decisions since it was started
    And a directory for import that checks clean
    When the operator imports the directory, saying which role they are
    Then the import is rejected because import goes only into a freshly started store

  Scenario: The operator imports the kb directory of an existing store
    Pins that a store's own directory imports as an export would, and that only its artifacts come across: its history and its marker stay behind.
    Given a freshly started store
    And the kb directory of an existing store, holding its types and artifacts, which check clean, together with its history and its store marker
    When the operator imports that kb directory, saying which role they are
    Then its types and artifacts land as they would from an export
    And its history and its store marker are passed over, neither landing in the store

  Scenario: Importing when nothing names the operator's role is refused
    Pins that an import is attributable like every other change, so nothing lands signed by nobody.
    Given a freshly started store, and nothing names which role the operator is
    And a directory for import that checks clean
    When the operator imports the directory
    Then the import is rejected because the role must be named through KB_ACTOR
    And nothing is written

  Scenario: The operator checks a directory for import and the store is left as it was
    Pins that checking is only a look: it changes nothing in the store.
    Given a store holding a decision
    And a directory for import
    When the operator checks the directory for import
    Then the store holds what it held before

  Scenario Outline: kb export and kb import find the store as kb validate does, with the same refusals
    Pins that exporting and importing name their store in the one way the command line already does, and are refused for the same reasons when it cannot be found.
    Given <where>
    When the operator runs <command> there
    Then <outcome>

    Examples:
      | where                                                                                                | command                                                                | outcome                                                                                                                             |
      | a store, with the operator working in a folder deep inside the directory it sits in                  | kb export to an empty directory                                        | the store found above where they are working is the one exported                                                                   |
      | a store, with the operator working outside any store and KB_ROOT naming that one                     | kb export to an empty directory                                        | the store KB_ROOT names is the one exported                                                                                         |
      | the operator is working outside any store and nothing names one                                      | kb export to an empty directory                                        | the export is rejected because no store was found, neither above where they are working nor named outright                         |
      | the operator is working outside any store, with KB_ROOT naming a directory that holds no store       | kb export to an empty directory                                        | the export is rejected because KB_ROOT names a directory that holds no store                                                       |
      | the operator is working inside a store, with KB_ROOT naming a different store                        | kb export to an empty directory                                        | the export is rejected because KB_ROOT names a store other than the one they are standing in, and neither of the two is guessed at |
      | a freshly started store, with the operator working in a folder deep inside the directory it sits in  | kb import of a directory that checks clean, saying which role they are | the store found above where they are working is the one imported into                                                              |
      | a freshly started store, with the operator working outside any store and KB_ROOT naming that one     | kb import of a directory that checks clean, saying which role they are | the store KB_ROOT names is the one imported into                                                                                    |
      | the operator is working outside any store and nothing names one                                      | kb import of a directory that checks clean, saying which role they are | the import is rejected because no store was found, neither above where they are working nor named outright                         |
      | the operator is working outside any store, with KB_ROOT naming a directory that holds no store       | kb import of a directory that checks clean, saying which role they are | the import is rejected because KB_ROOT names a directory that holds no store                                                       |
      | the operator is working inside a store, with KB_ROOT naming a different store                        | kb import of a directory that checks clean, saying which role they are | the import is rejected because KB_ROOT names a store other than the one they are standing in, and neither of the two is guessed at |

  Scenario: Importing with errors skipped when nothing would land is refused
    Pins that skipping errors never turns into an import that brings nothing, reported as if it had worked.
    Given a freshly started store
    And a directory for import in which every file has an error
    When the operator imports the directory with errors skipped, saying which role they are
    Then the import is rejected because nothing would land
    And nothing is written

  Scenario: The operator imports a directory whose type that describes types matches the store's
    Pins that a directory's copy of the type that describes types, when it matches, is not imported over the store's own.
    Given a freshly started store
    And a directory for import that checks clean, holding a copy of the type that describes types that matches the store's
    When the operator imports the directory, saying which role they are
    Then the directory's copy of the type that describes types is passed over
    And the store's type that describes types is kept as it was

  Scenario: The operator checks a directory for import whose type that describes types differs from the store's
    Pins that a directory cannot quietly bring a different type that describes types: a copy that differs is an error, named by its file.
    Given a freshly started store
    And a directory for import holding a copy of the type that describes types that differs from the store's
    When the operator checks the directory for import
    Then the file holding that copy is reported as an error, naming the file
