# formulated from spec/capabilities/make-several-changes-in-one-go.md
Feature: Make several changes in one go
  Narrator: the client

  Background:
    Given a store holding a decision type and a work item

  @slice-121
  Scenario: A client that needs a create and a replacement makes two calls
    Pins that a set is one kind of change: a create and a replacement are two sets, each landing and each named in the history as its own.
    When the client asks, in one go, for a decision to be created, saying which role and why
    And the client then asks, in one go, for the work item to be replaced so that it points at that decision, saying which role and why
    Then both sets land
    And the history shows two sets, the create's and the replacement's

  @slice-121
  Scenario: The client makes several changes in one go
    Pins that a set of changes is one act: the store names the set itself, each change still reports its own result, and the history shows one change rather than several.
    When the client asks, in one go, for a decision and a work item to be created, in that order, saying which role and why
    Then the client is given one name for the set, which the client never asked for
    And each change also comes back with its own result
    And the store's history shows the set as one change

  @slice-121
  Scenario: The name given for a set finds the set in the history
    Pins that the name handed back is the one the history uses, so a client can go from having made a set to seeing exactly what it did.
    When the client asks, in one go, for a decision and a work item to be created, in that order, saying which role and why
    Then the changes the history shows under the name the client was given for the set are exactly those two

  @slice-6
  Scenario: One bad change in a set leaves the store untouched
    Pins that a set is all or nothing, and that the refusal still accounts for every fault so the whole set can be fixed in one more attempt.
    Given a set whose second change is missing a section its type requires
    When the client asks for the set, saying which role and why
    Then the set is rejected because a change in it does not fit its type
    And the store holds neither change
    And every fault in the set comes back, not only the first

  @slice-126
  Scenario: A change in a set refused with several faults has them given in the order its places stand when its artifact reads back
    Pins that inside a set one change's faults follow the order its artifact would read back, not the order the client wrote it in, and that faults at one place are told apart by a fixed order of their rules.
    Given the decision type declares its fields first, then its required sections, then its collection of options
    And a set whose second change is a decision written with its options first, then its sections, then its fields, where a field breaks two rules of the type, the second option is of a shape the type does not allow, and the rationale is missing
    When the client asks for the set, saying which role and why
    Then the set is rejected because a change in it does not fit its type
    And that change's faults come in the order the places stand in its artifact as it would read back: the field first, then the sections, then the options
    And the two faults at the field come in the alphabetical order of the names of the rules they break

  @slice-126
  Scenario: Faults of several refused changes in a set come in the order of the set
    Pins that a set's refusal reads in the order the client wrote the set, so a client can match each fault to its change without searching.
    Given a set whose first and second changes are each missing a section its type requires
    When the client asks for the set, saying which role and why
    Then the set is rejected because a change in it does not fit its type
    And the first change's fault comes back before the second change's fault

  @slice-85
  Scenario Outline: A set stopped for any reason at all leaves the store exactly as it was
    Pins all-or-nothing for every way a set can be stopped, not only a change that does not fit: the whole set is worked out and checked before anything is written, so nothing ever half-lands.
    When the client asks, in one go, for a set in which <fault>, saying which role and why
    Then the set is rejected because <reason>
    And the store holds none of the changes in the set
    And the store's history holds no entry for any of them

    Examples:
      | fault                                                                | reason                                                                  |
      | the second change names an artifact the store holds nothing under    | the store holds nothing by that name, and the name asked for is given back |
      | the second change removes an artifact something still points at      | something still points at it                                            |

  @slice-97
  Scenario: A set holding no changes at all is refused
    Pins that a set is a request to change something, so asking for nothing is a mistake the client is told about rather than a change the store records, and the store is left exactly as it was.
    When the client asks, in one go, for a set holding no changes at all, saying which role and why
    Then the set is rejected because a set must hold at least one change
    And the store holds no artifact it did not hold before
    And the store's history holds no entry for it

  @slice-70
  Scenario: Two changes to one artifact in one set each leave their own entry
    Pins that a set is still a set of changes: each one counts the artifact's version up and is recorded on its own, even though the set as a whole lands once.
    When the client asks, in one go, for the work item to be changed twice, saying which role and why
    Then the store's history holds an entry for each of the two changes
    And each entry records the version that change left behind
    And the work item's version has gone up by two

  @slice-121
  Scenario Outline: A create in a set points at what another create in it makes, earlier or later
    Pins that a link may point at what any create in the set makes, before or after it, because links are judged against the store as the whole set leaves it.
    When the client asks, in one go, for <creates>, in that order, saying which role and why
    Then the set lands, and the new work item points at the new decision

    Examples:
      | creates                                                                                                                 |
      | a decision to be created carrying a key and a work item to be created pointing at it by that key                        |
      | a work item to be created pointing at a decision by the key its create carries and that decision to be created with it |

  @slice-121
  Scenario Outline: A link in a set that refers to the key a create carries points at what that create makes
    Pins that a key is only the client's handle inside the set: the link lands on the artifact the create makes, and what the store keeps is the name it gave that artifact, wherever in the set the link is written.
    Given work items may carry a collection of tasks, each of which may point at a decision
    When the client asks, in one go, for a decision to be created carrying a key of the client's choosing and a work item to be created with a link to that key <where>, saying which role and why
    Then the new work item points, <where>, at the decision that create made
    And the link holds the name the store gave the decision, not the key

    Examples:
      | where                    |
      | in its content           |
      | inside one of its tasks  |

  @slice-121
  Scenario: Two new artifacts in one set that point at each other by their keys land
    Pins that a set is checked as a whole, so two artifacts that each need the other to exist can be made together, which no order of single changes allows.
    Given the decision type lets a decision point at another decision
    When the client asks, in one go, for two decisions to be created, each carrying a key and pointing at the other by the key the other's create carries, saying which role and why
    Then the set lands
    And the store holds both decisions, each pointing at the other

  @slice-121
  Scenario: Each create in a set gives back the name it was given, in the order of the set
    Pins that a client which made several artifacts at once can tell which name went to which, without reading the store again.
    When the client asks, in one go, for three decisions with titles of their own to be created, saying which role and why
    Then the client is given a result for each create, in the order of the set
    And each result gives the name the store gave the decision made by the create in that place

  @slice-121
  Scenario: A link in a set that refers to a key no create in it carries is refused
    Pins that a key is never looked for outside its set, so a link whose key no create carries points at nothing and the whole set is stopped.
    When the client asks, in one go, for a decision and a work item to be created, the work item pointing at a key no create in the set carries, saying which role and why
    Then the set is rejected because the link lands on nothing
    And the key is given back
    And the store holds none of the changes in the set

  @slice-121
  Scenario: Two creates in one set that carry the same key are refused
    Pins that a key names one create only, so a link to it can never be taken to mean either of two artifacts.
    When the client asks, in one go, for two decisions to be created, both carrying the same key, saying which role and why
    Then the set is rejected because a key names one create in the set
    And the key is given back
    And the store holds none of the changes in the set

  @slice-121
  Scenario: A link in a set that refers to a key together with a place inside what that create makes is refused
    Pins that a key stands for a whole new artifact and nothing inside it, so a link that reaches past it into a place lands on nothing.
    When the client asks, in one go, for a decision to be created carrying a key and a work item to be created pointing at that key together with a place inside the decision, saying which role and why
    Then the set is rejected because the link lands on nothing
    And the reference is given back
    And the store holds none of the changes in the set

  @slice-122
  Scenario Outline: A change in a set that says a version its artifact no longer stands at is refused
    Pins that a client which says what it read is never allowed to overwrite what it did not see, and that one such change stops its whole set.
    Given the store also holds a second work item, and work items carry a collection of tasks
    And the client read the work item at its first version, and another client has since replaced it
    When the client asks, in one go, for <changes>, the change to the work item saying the version the client read it at, saying which role and why
    Then the set is rejected because the artifact moved since it was read
    And the version the work item stands at is given back
    And nothing of the set is written

    Examples:
      | changes                                                             |
      | the work item and the second work item to be replaced               |
      | a task to be added to the work item and one to the second work item |
      | the work item and the second work item to be removed                |

  @slice-122
  Scenario Outline: The second change to one artifact in a set is held to the version the first one left
    Pins that within a set the version a change says is compared with what the changes before it left, not with the store before the set, so a client can chain changes to one artifact in one go.
    When the client asks, in one go, for the work item to be replaced twice, the second replacement saying <version>, saying which role and why
    Then <outcome>

    Examples:
      | version                                           | outcome                                                          |
      | the version the first replacement leaves          | the set lands, and the work item's version has gone up by two    |
      | the version the work item stood at before the set | the set is rejected because the artifact moved since it was read |

  @slice-121
  Scenario: A set that waits longer than the store waits for another change is refused as busy
    Pins that a set is held to the same wait as a single change: refused as busy, none of it written, and free to be asked for again.
    Given another change is being written and holds the store longer than the store waits
    When the client asks, in one go, for a decision and a work item to be created, in that order, saying which role and why
    Then the set is rejected because the store was busy with another change
    And nothing is written
    And the same set may be asked for again
