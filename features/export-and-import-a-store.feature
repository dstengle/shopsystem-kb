# formulated from spec/capabilities/export-and-import-a-store.md
Feature: Export and import a store
  Narrator: the operator

  @slice-174
  Scenario Outline: The operator exports the store to a directory that is empty or does not exist
    Pins what an export is: one readable file per artifact placed by its IRI, a type written only as its versions, each version as it stood, saying who the artifact is before what it holds, all taken from a single moment of the store.
    Given a store holding a type for decisions at two versions, a type for work items at one version, two decisions and a work item
    And a directory for the export that <state>
    When the operator exports the store to that directory
    Then the directory holds one file for each decision and for the work item, at a place that follows the path of its IRI
    And for each type the directory holds one file for each version the store holds and no other, at the type's place followed by @ and the version's number
    And each version's file gives that version's own revision and title
    And each file gives the artifact's identity first, its IRI, the IRI of the version of its type it conforms to, its revision and its title, and then its content
    And every file shows the store as it stood at one moment

    Examples:
      | state          |
      | is empty       |
      | does not exist |

  @slice-110
  Scenario: The operator opens an exported artifact's file
    Pins that the exported files are meant to be read and reviewed by people: prose in blocks, lists under their names, no rewrapping, and nothing in them that instructs a reader how to build a value.
    Given a store holding a decision whose purpose is one short line and which carries a list of options, exported to a directory
    When the operator opens the decision's exported file
    Then every piece of prose stands as a block of its own, however short it is
    And each list is written beneath the name it belongs to, indented under it
    And no line of prose has been broken to fit a width
    And nothing in the file tells a reader how to build a value

  @slice-110
  Scenario: Two stores given the same content by the same client are exported
    Pins that exporting is deterministic, which is what makes a difference between two exports mean a real change rather than a reshuffle.
    Given two stores each given the same decision by the same client, and each exported to a directory of its own
    When the operator compares the two exported decision files
    Then the two files are the same, byte for byte

  @slice-110
  Scenario: Exporting to a directory that holds anything is refused
    Pins that an export never writes over what is already there.
    Given a store holding a decision
    And a directory that already holds a file
    When the operator exports the store to that directory
    Then the export is rejected because export never overwrites
    And what the directory holds is left as it was

  @slice-118.2
  Scenario: Exporting to something that is a file, not a directory, is refused
    Pins that an export is written into a directory and never into a file, and that the file in the way is not touched.
    Given a store holding a decision
    And a file where the export is to go, and no directory
    When the operator exports the store to that file
    Then the export is rejected because export writes into a directory
    And the file is left as it was

  @slice-118.2
  Scenario: Checking for import something that is not a directory is refused
    Pins that files for import are read only from a directory, so a check pointed at anything else is refused rather than run.
    Given a store
    And a file where a directory for import should be
    When the operator checks that file for import
    Then the check is rejected because files for import are read from a directory
    And nothing is written

  @slice-118.2
  Scenario: Importing from something that is not a directory is refused
    Pins that an import reads only from a directory, so one pointed at anything else is refused and takes nothing.
    Given a freshly started store
    And a file where a directory for import should be
    When the operator imports that file, saying which role they are
    Then the import is rejected because files for import are read from a directory
    And nothing is written

  @slice-183
  Scenario Outline: The operator checks a directory for import and each error is reported by file and reason
    Pins that the check reads every file rather than stopping at the first fault, and that each fault names the file it is in and the reason it is one.
    Given a store
    And a directory for import holding well-formed files and two files that each <fault>
    When the operator checks the directory for import
    Then each of the two files is reported as an error, naming the file, with the reason that <reason>

    Examples:
      | fault                                                                            | reason                                                                              |
      | cannot be read as YAML 1.2                                                       | it cannot be read as YAML 1.2                                                       |
      | is not in canonical form                                                         | it is not in canonical form                                                         |
      | claims a type neither the directory nor the store holds                          | it claims a type neither the directory nor the store holds                          |
      | has content that does not fit its type                                           | its content does not fit its type                                                   |
      | carries a link to an IRI under a type neither the directory nor the store holds  | it carries a link to an IRI under a type neither the directory nor the store holds  |

  @slice-182
  Scenario Outline: The operator checks a directory for import holding an artifact the store holds at the same IRI with other content or another type version
    Pins that the check finds, before anything lands, every file that would bring a different artifact under an IRI the store already holds.
    Given a store holding a type for decisions at version 2 and two decisions written against version 2
    And a directory for import holding both decisions at the same IRIs, each <difference>
    When the operator checks the directory for import
    Then each of the two decisions is reported as an error, naming its IRI

    Examples:
      | difference                                                                 |
      | with other content, written against version 2 of the type for decisions    |
      | with the same content, written against version 1 of the type for decisions |

  @slice-184
  Scenario Outline: The operator checks a directory for import that holds a type version's file with an error
    Pins a broken type version's reach: the type versions built on it, however indirectly, and the artifacts written against it or against any of them, are named as ones that would be skipped, with the way each leads there.
    Given a store
    And a directory for import holding version 2 of a type for decisions, whose content does not fit the type that describes types, and <leading>
    When the operator checks the directory for import
    Then <skipped> reported as a file that would be skipped, each with the chain that leads from it to the broken file

    Examples:
      | leading                                                                                                                                                                                                                                  | skipped                                                                                |
      | a decision conforming to version 2 of the type for decisions                                                                                                                                                                             | the decision is                                                                        |
      | version 1 of a type for notes, which refers to version 2 of the type for decisions by a kb: reference, and a note conforming to version 1 of the type for notes                                                                          | version 1 of the type for notes and the note are                                       |
      | version 1 of a type for notes, which refers to version 2 of the type for decisions by a kb: reference, version 1 of a type for tasks, which refers to version 1 of the type for notes by a kb: reference, and a task conforming to version 1 of the type for tasks | version 1 of the type for notes, version 1 of the type for tasks and the task are      |

  @slice-111
  Scenario: The operator checks a directory for import that holds no error
    Pins that a clean directory is said to be clean.
    Given a store
    And a directory for import in which every file is well formed, fits its type and links only to what is there
    When the operator checks the directory for import
    Then the check reports success

  @slice-111
  Scenario: A directory checked for import holds an error
    Pins that any error at all makes the check fail, so a directory with one is never taken as fit to import.
    Given a store
    And a directory for import holding one file whose content does not fit its type
    When the operator checks the directory for import
    Then the check reports failure

  @slice-181
  Scenario: The operator imports a directory that checks clean into a store, saying which role they are
    Pins that an import goes into a store already holding artifacts, lands whole as one signed change saying where it came from, and that each artifact arrives as it was rather than as something new.
    Given a store holding a type for work items and a work item
    And a directory for import that checks clean, holding both versions of a type for decisions and a decision at revision 3 written against version 2 of the type for decisions
    When the operator imports the directory, saying which role they are
    Then everything in the directory lands as one set, signed by that role, with a message naming the directory
    And the decision lands at the same IRI and with the same title, at revision 3, written against version 2 of the type for decisions
    And the type for decisions lands at the same IRI and with the same title, at the revision and type version the directory gives it

  @slice-181
  Scenario: The operator imports a directory that checks clean, and the history shows each type landing before its artifacts
    Pins the order an import lands in and what it adds to the history: one import entry per artifact, a type always ahead of the artifacts of its kind.
    Given a store holding a type for notes and a note
    And a directory for import that checks clean, holding a type for decisions and a type for work items, each at one version, two decisions and a work item
    When the operator imports the directory, saying which role they are
    Then the store's history gains one import entry for each of the five artifacts
    And in the history each type's import entry comes before the import entries of the artifacts of its kind

  @slice-181
  Scenario: The operator imports a directory holding an artifact the store already holds at the same IRI, with the same content and the same type version
    Pins that bringing in again what the store already holds identically is no obstacle: that artifact is left alone and everything else comes in.
    Given a store holding a type for decisions and a decision
    And a directory for import that checks clean, holding that decision at the same IRI with the same content and the same type version, and a second decision
    When the operator imports the directory, saying which role they are
    Then the decision the store held is passed over, left as the store held it
    And the second decision lands

  @slice-182
  Scenario Outline: Importing a directory holding an artifact the store already holds at the same IRI with other content or another type version is refused
    Pins that an import never replaces what the store holds: any differing artifact stops the whole import, and the operator is told every IRI that differs.
    Given a store holding a type for decisions at version 2 and two decisions written against version 2
    And a directory for import holding both decisions at the same IRIs, each <difference>, and a third decision the store does not hold
    When the operator imports the directory, saying which role they are
    Then the import is rejected, naming the IRI of each of the two decisions
    And nothing lands, the third decision included

    Examples:
      | difference                                                                 |
      | with other content, written against version 2 of the type for decisions    |
      | with the same content, written against version 1 of the type for decisions |

  @slice-183
  Scenario Outline: The operator imports a directory holding a link to an IRI neither the directory nor the store holds, under a type one of them holds that the link field allows
    Pins that a link to something not yet anywhere does not stop an import: it lands and waits on a placeholder, whether the directory or the store holds the type it names.
    Given a store holding a type for work items whose link field allows decisions
    And a type for decisions held by <holder>
    And a directory for import that checks clean, holding a work item whose link names an IRI under the type for decisions that neither the directory nor the store holds
    When the operator imports the directory, saying which role they are
    Then the import lands
    And the work item's link lands on a placeholder at that IRI

    Examples:
      | holder        |
      | the store     |
      | the directory |

  @slice-112
  Scenario: Importing a directory that holds an error is refused
    Pins that import always checks first and takes nothing from a directory whose check fails, showing the operator why.
    Given a freshly started store
    And a directory for import holding one file whose content does not fit its type
    When the operator imports the directory, saying which role they are
    Then the import is rejected because the check found errors
    And the operator is shown the check's report
    And nothing is written

  @slice-184
  Scenario Outline: The operator imports with errors skipped
    Pins that skipping errors leaves out exactly the broken files, the type versions built on a broken type version and the artifacts written against any of them, lands everything else, lets a link to what was left out wait on a placeholder, and says what was left out and why.
    Given a freshly started store
    And a directory for import holding a type for work items whose link field allows decisions, and a work item, together with <broken>
    When the operator imports the directory with errors skipped, saying which role they are
    Then the type for work items and the work item land
    And <left out> do not land
    And <rest>
    And the operator is told what was skipped and why

    Examples:
      | broken                                                                                                                                                                                                                                                                                  | left out                                                    | rest                                                                                                  |
      | a type for decisions, a decision with an error, and a second decision that links to it                                                                                                                                                                                                  | the decision with an error                                  | the second decision lands, its link landing on a placeholder at the IRI of the decision with an error |
      | version 1 of a type for decisions whose content does not fit the type that describes types, and a decision conforming to it that the work item links to                                                                                                                                | the type version and the decision                           | the work item's link to the decision lands on a placeholder at the decision's IRI                     |
      | version 1 of a type for decisions whose content does not fit the type that describes types, version 1 of a type for notes, which refers to it by a kb: reference, and a note conforming to version 1 of the type for notes                                                             | the two type versions and the note                          | every other file in the directory lands                                                               |
      | version 1 of a type for decisions whose content does not fit the type that describes types, version 1 of a type for notes, which refers to it by a kb: reference, version 1 of a type for tasks, which refers to that one by a kb: reference, and a task conforming to version 1 of the type for tasks | the three type versions and the task                        | every other file in the directory lands                                                               |

  @slice-112
  Scenario: The operator imports the kb directory of an existing store
    Pins that a store's own directory imports as an export would, and that only its artifacts come across: its history and its marker stay behind.
    Given a freshly started store
    And the kb directory of an existing store, holding its types and artifacts, which check clean, together with its history and its store marker
    When the operator imports that kb directory, saying which role they are
    Then its types and artifacts land as they would from an export
    And its history and its store marker are passed over, neither landing in the store

  @slice-112
  Scenario: Importing when nothing names the operator's role is refused
    Pins that an import is attributable like every other change, so nothing lands signed by nobody.
    Given a freshly started store, and nothing names which role the operator is
    And a directory for import that checks clean
    When the operator imports the directory
    Then the import is rejected because the role must be named through KB_ACTOR
    And nothing is written

  @slice-111
  Scenario: The operator checks a directory for import and the store is left as it was
    Pins that checking is only a look: it changes nothing in the store.
    Given a store holding a decision
    And a directory for import
    When the operator checks the directory for import
    Then the store holds what it held before

  @slice-112
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

  @slice-112
  Scenario: Importing with errors skipped when nothing would land is refused
    Pins that skipping errors never turns into an import that brings nothing, reported as if it had worked.
    Given a freshly started store
    And a directory for import in which every file has an error
    When the operator imports the directory with errors skipped, saying which role they are
    Then the import is rejected because nothing would land
    And nothing is written

  @slice-112
  Scenario: The operator imports a directory whose type that describes types matches the store's
    Pins that a directory's copy of the type that describes types, when it matches, is not imported over the store's own.
    Given a freshly started store
    And a directory for import that checks clean, holding a copy of the type that describes types that matches the store's
    When the operator imports the directory, saying which role they are
    Then the directory's copy of the type that describes types is passed over
    And the store's type that describes types is kept as it was

  @slice-111
  Scenario: The operator checks a directory for import whose type that describes types differs from the store's
    Pins that a directory cannot quietly bring a different type that describes types: a copy that differs is an error, named by its file.
    Given a freshly started store
    And a directory for import holding a copy of the type that describes types that differs from the store's
    When the operator checks the directory for import
    Then the file holding that copy is reported as an error, naming the file

  @slice-115
  Scenario: An import that waits longer than the store waits for another change is refused as busy
    Pins that an import, which writes, is held to the same wait as any change: refused as busy, nothing written, free to be run again.
    Given a freshly started store
    And a directory for import that checks clean
    And another change is being written and holds the store longer than the store waits
    When the operator imports the directory, saying which role they are
    Then the import is rejected because the store was busy with another change
    And nothing is written
    And the same import may be run again

  @slice-115
  Scenario: The operator exports the store while another change is being written
    Pins that an export is a read: it is written however long another change holds the store.
    Given a store holding a decision
    And another change is being written and holds the store longer than the store waits
    When the operator exports the store to an empty directory
    Then the export is written
    And the export is not refused because the store was busy with another change
