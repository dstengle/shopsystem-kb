# formulated from spec/capabilities/name-what-is-asked-for.md
Feature: Name what is asked for
  Narrator: the client

  @slice-1.7
  Scenario: A name that is not a plain name is refused
    Pins that a name is checked for shape before any file is found from it, so a name built to walk out of the store reads nothing at all.
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    When the client reads an artifact by the name "decision/../elsewhere"
    Then the read is rejected because a name is a kind and a plain name of lower-case letters, digits and single hyphens
    And no content comes back, from inside the store or outside it

  @slice-1.7
  Scenario: A name that begins at the root of the disk is refused
    Pins the same for a name that is simply a path from the top of the disk, which is the other obvious way to ask for a file that is none of the store's business.
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    When the client reads an artifact by a name that begins at the root of the disk
    Then the read is rejected because a name is a kind and a plain name, never a path
    And no content comes back, from inside the store or outside it

  @slice-1.7
  Scenario: A place inside an artifact that is not a plain place is refused
    Pins that the place inside an artifact is checked just as strictly as the name, so nothing escapes through the second half of a locator.
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    When the client reads the place "sections/../.." inside the decision
    Then the read is rejected because a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it
    And no content comes back, from inside the store or outside it

  @slice-23
  Scenario: A change aimed at a name that is not a plain name writes nothing
    Pins that a name is checked for shape before any file is worked out from it, so a name dressed up as a path can never reach the disk, inside the store or out.
    Given a store holding a decision with a purpose and a rationale, at its first version
    When the client replaces an artifact named "../../elsewhere", saying which role and why
    Then the change is rejected because a name is a kind and a plain name of lower-case letters, digits and single hyphens
    And nothing is written anywhere, inside the store or outside it

  @slice-1.14
  Scenario: A kind that is not a plain name is refused
    Pins that the kind is checked for shape before anything is looked up or worked out from it, so a kind shaped like a path never reaches the disk.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates an artifact of the kind "../schema/decision", with a title and both required sections, saying which role and why
    Then the artifact is rejected because a kind is a plain name of lower-case letters, digits and single hyphens, never a path
    And nothing is looked up or written anywhere, inside the store or outside it

  @slice-1.7
  Scenario: Reading something the store does not hold is refused
    Pins that a name the store does not know is an answer that names it back, so a client can tell "not here" from "went wrong".
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items
    When the client reads an artifact by a name the store holds nothing under
    Then the read is rejected because the store holds nothing by that name, and the name asked for is given back

  @slice-23
  Scenario: Changing something the store does not hold is refused
    Pins that writing to an unknown name is an answer, not an accident: it names what was asked for and creates nothing.
    Given a store holding a decision with a purpose and a rationale, at its first version
    When the client replaces an artifact by a name the store holds nothing under, saying which role and why
    Then the change is rejected because the store holds nothing by that name, and the name asked for is given back
    And nothing is written anywhere in the store

  @slice-39
  Scenario: Adding an item to something the store does not hold is refused
    Pins that a missing artifact is an ordinary answer naming the name asked for, not a crash, and that the refused add writes nothing.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step to a process by a name the store holds nothing under, saying which role and why
    Then the item is rejected because the store holds nothing by that name, and the name asked for is given back
    And nothing is written anywhere in the store

  @slice-41
  Scenario: Removing something the store does not hold is refused
    Pins that removing what is not there is an answer naming what was asked for, rather than a success that silently did nothing.
    Given a store holding a tag nothing points at
    And a tag a decision points at
    When the client removes an artifact by a name the store holds nothing under, saying which role and why
    Then the removal is rejected because the store holds nothing by that name, and the name asked for is given back
    And the store holds what it held before

  @slice-88
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

  @slice-65
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

  @slice-1.25
  Scenario: A kind the store holds no type for is refused
    Pins that an unknown kind is its own plain answer, named back and kept apart from any complaint about the content, so a client can tell a typo from a bad artifact.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    Given a store that holds no type called "invoice"
    When the client creates an artifact of the kind "invoice", with a title and both required sections, saying which role and why
    Then the artifact is rejected because a kind must name a type the store holds, and the kind asked for is given back
    And that fault stands on its own, apart from anything wrong with the content
    And nothing is written anywhere in the store

  @slice-82
  Scenario Outline: Asking by a kind the store holds no type for is refused
    Pins that an unknown kind is the same plain refusal wherever it is asked for, so a typo is never answered with an empty result that reads exactly like an empty store.
    Given a store holding three decisions, one of them superseded
    Given a store that holds no type called "invoice"
    When the client <call>
    Then the call is rejected because a kind must name a type the store holds, and the kind asked for is given back

    Examples:
      | call                                                              |
      | lists the artifacts of the kind "invoice"                         |
      | searches the prose for restocking among artifacts of that kind    |
      | follows the links into a decision, only from artifacts of that kind |
