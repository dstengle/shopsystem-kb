# formulated from spec/capabilities/name-what-is-asked-for.md
Feature: Name what is asked for
  Narrator: the client

  @slice-178 @r1
  Scenario Outline: A name a call carries is an IRI of kb's grammar
    Pins each rule of kb's grammar for a name, and the length it may run to, so a name broken in any one way is refused for its shape before anything is looked up.
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    When the client reads an artifact by <name>
    Then the read is rejected because <reason>

    Examples:
      | name                                                                              | reason                                    |
      | the decision's IRI with the scheme "http"                                         | a name is an IRI of kb's grammar          |
      | the decision's IRI with its host in upper case                                    | a name is an IRI of kb's grammar          |
      | the decision's IRI with two dots together in its host                             | a name is an IRI of kb's grammar          |
      | the decision's IRI with a segment holding an upper-case letter                    | a name is an IRI of kb's grammar          |
      | the decision's IRI with a segment holding two hyphens together                    | a name is an IRI of kb's grammar          |
      | the decision's IRI with an empty segment in its path                              | a name is an IRI of kb's grammar          |
      | the decision's IRI followed by a query                                            | a name is an IRI of kb's grammar          |
      | the decision's IRI followed by a slash                                            | a name is an IRI of kb's grammar          |
      | the decision's IRI with a segment percent-encoded                                 | a name is an IRI of kb's grammar          |
      | a name of 513 characters, otherwise of kb's grammar                               | a name is an IRI of kb's grammar          |
      | a name of 512 characters, of kb's grammar, that the store holds nothing under     | the store holds nothing by that name      |
      | the decision's IRI with "@" in its host                                           | a name is an IRI of kb's grammar          |
      | the decision's IRI holding "#" twice                                              | a name is an IRI of kb's grammar          |

  @slice-178 @r2
  Scenario: A read by a name that is not an IRI of kb's grammar is refused
    Pins that a name is checked for shape before any file is found from it, so a name built to walk out of the store reads nothing at all.
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    When the client reads an artifact by a name whose path holds ".."
    Then the read is rejected because a name is an IRI of kb's grammar, and the name asked for is given back
    And no content comes back, from inside the store or outside it

  @slice-178 @r3
  Scenario: A read by a name that is a path on the disk is refused
    Pins that a path on the disk is never taken for a name, the other obvious way to ask for a file that is none of the store's business.
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    When the client reads an artifact by the name "/etc/passwd"
    Then the read is rejected because a name is an IRI, never a path
    And no content comes back, from inside the store or outside it

  @slice-1.7 @r4
  Scenario: A place inside an artifact that is not a plain place is refused
    Pins that the place inside an artifact is checked just as strictly as the name, so nothing escapes through the second half of a locator.
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    When the client reads the place "sections/../.." inside the decision
    Then the read is rejected because a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it
    And no content comes back, from inside the store or outside it

  @slice-178 @r5
  Scenario: A change by a name that is not an IRI of kb's grammar writes nothing
    Pins that a change's name is checked for shape before anything is worked out from it, so a name dressed up as a path never reaches the disk.
    Given a store holding a decision with a purpose and a rationale, at its first version
    When the client replaces an artifact by a name whose path holds "..", saying which role and why
    Then the change is rejected because a name is an IRI of kb's grammar, and the name asked for is given back
    And nothing is written anywhere, inside the store or outside it

  @slice-178 @r6
  Scenario: A create naming a version of a type not shaped as a type's IRI, "@" and a number is refused
    Pins that the version a create names is checked for shape before anything is looked up from it, so a version shaped like a path never reaches the disk.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates an artifact naming the version of a type "../schema/decision@1", with a title and both required sections, saying which role and why
    Then the artifact is rejected because a version of a type is named by the type's IRI, "@" and its number
    And nothing is looked up or written anywhere, inside the store or outside it

  @slice-1.7 @r7
  Scenario: Reading something the store does not hold is refused
    Pins that a name the store does not know is an answer that names it back, so a client can tell "not here" from "went wrong".
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    When the client reads an artifact by a name the store holds nothing under
    Then the read is rejected because the store holds nothing by that name, and the name asked for is given back

  @slice-166 @r8
  Scenario: A read by an IRI links point at that the store does not hold is refused
    Pins that being pointed at by a link does not make a name held, so reading where a link points is the same plain "not here" as any other unheld name.
    Given a store holding a decision that links to an IRI the store does not hold
    When the client reads an artifact by that IRI
    Then the read is rejected because the store holds nothing by that name, and the name asked for is given back

  @slice-23 @r9
  Scenario: Changing something the store does not hold is refused
    Pins that writing to an unknown name is an answer, not an accident: it names what was asked for and creates nothing.
    Given a store holding a decision with a purpose and a rationale, at its first version
    When the client replaces an artifact by a name the store holds nothing under, saying which role and why
    Then the change is rejected because the store holds nothing by that name, and the name asked for is given back
    And nothing is written anywhere in the store

  @slice-39 @r10
  Scenario: Adding an item to something the store does not hold is refused
    Pins that a missing artifact is an ordinary answer naming the name asked for, not a crash, and that the refused add writes nothing.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step to a process by a name the store holds nothing under, saying which role and why
    Then the item is rejected because the store holds nothing by that name, and the name asked for is given back
    And nothing is written anywhere in the store

  @slice-41 @r11
  Scenario: Removing something the store does not hold is refused
    Pins that removing what is not there is an answer naming what was asked for, rather than a success that silently did nothing.
    Given a store holding a tag nothing points at
    And a tag a decision points at
    When the client removes an artifact by a name the store holds nothing under, saying which role and why
    Then the removal is rejected because the store holds nothing by that name, and the name asked for is given back
    And the store holds what it held before

  @slice-88 @r12
  Scenario Outline: A read that names a place the artifact does not hold is refused
    Pins that naming a place that is not there is an ordinary answer naming what was asked for, so a client can tell "not here" from "went wrong" inside an artifact as well as between artifacts.
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    When the client reads <what>
    Then the read is rejected because the decision holds nothing at that place, and what was asked for is given back
    And no content comes back

    Examples:
      | what                                                                        |
      | the section of the decision titled "Consequences", which it holds no section under |
      | the place "sections/nowhere" inside the decision                            |
      | the place "sections/purpose/body/first" inside the decision, which runs on past a piece of prose |

  @slice-65 @r13
  Scenario Outline: Every way the place a change is aimed at can be wrong is refused
    Pins that the place inside an artifact is checked before anything is touched, so a change that names nothing real is a plain refusal and the artifact is left exactly as it was.
    Given a store holding a decision with a purpose and a rationale, at its first version
    When the client <call>, saying which role and why
    Then the change is rejected because <reason>
    And reading the decision gives what it held before, at the version it held before

    Examples:
      | call                                                                       | reason                                                           |
      | replaces a place inside the decision the decision holds nothing under      | the decision holds nothing at that place                         |
      | replaces a place inside the decision that runs on past a piece of prose    | the decision holds nothing at that place                         |
      | replaces a place inside the decision beginning at the decision's own version | a place inside an artifact never names what only the store settles |
      | adds an item at a place inside the decision that is not a collection       | an item is added to a collection, and that place is not one      |

  @slice-162 @r14
  Scenario Outline: A create naming a type version the store does not hold is refused
    Pins that an unheld version is its own plain answer, named back and kept apart from any complaint about the content, whether the store holds the type at another version or not at all.
    Given a store holding a decision type, at its first version, whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    And a store that holds no type for the kind "invoice"
    When the client creates an artifact naming <version>, with a title and both required sections, saying which role and why
    Then the artifact is rejected because a create names a version of a type the store holds, and the version asked for is given back
    And that fault stands on its own, apart from anything wrong with the content
    And nothing is written anywhere in the store

    Examples:
      | version                                                  |
      | the decision type at its second version, which the store does not hold |
      | the invoice type at its first version                    |

  @slice-176 @r15
  Scenario Outline: Listing, searching, following links or exporting by a kind the store holds no type for is refused
    Pins that an unknown kind is the same plain refusal wherever it is asked for, export included, so a typo is never answered with an empty result that reads like an empty store.
    Given a store holding three decisions, one of them superseded
    And a store that holds no type for the kind "invoice"
    When the client <call>
    Then the call is rejected because a kind must name a type the store holds, and the kind asked for is given back

    Examples:
      | call                                                                |
      | lists the artifacts of the kind "invoice"                           |
      | searches the prose for restocking among artifacts of that kind      |
      | follows the links into a decision, only from artifacts of that kind |
      | exports only the artifacts of that kind                             |

  @slice-178 @r16
  Scenario: A read by an IRI under no type the store holds is refused
    Pins that a name under no held type is the same plain "not here" as any unheld name, named back rather than a failure.
    Given a store holding three decisions, one of them superseded
    When the client reads an artifact by an IRI under no type the store holds
    Then the read is rejected because the store holds nothing by that name, and the name asked for is given back
