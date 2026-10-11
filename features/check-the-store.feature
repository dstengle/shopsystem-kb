# formulated from spec/capabilities/check-the-store.md
Feature: Check the store
  Narrator: the client

  @slice-43
  Scenario: A store with nothing wrong reports nothing
    Pins the quiet case: a healthy store says so plainly, so silence is a real answer rather than a check that did not run.
    Given a store where everything fits its type
    When the client checks the store
    Then the client is told of no violation

  @slice-170
  Scenario: Every violation is reported
    Pins that a check sweeps the whole store and reports every fault it finds, each placed precisely, rather than stopping at the first.
    Given a store where one artifact is missing a section its type requires and another holds a field of a shape its type does not allow
    When the client checks the store
    Then both are reported, each naming the artifact, the place in it and the rule broken

  @slice-126
  Scenario: An artifact's violations are given in the order its places stand when it reads back
    Pins that a check reports one artifact's violations in the order the artifact reads back, whatever order they were stored in, and tells apart violations at one place by a fixed order of their rules.
    Given a store holding a decision type that declares its fields first, then its required sections, then its collection of options
    And the store holds a decision stored with its options first, then its sections, then its fields, where a field breaks two rules of the type, the second option is of a shape the type does not allow, and the rationale is missing
    When the client checks the store
    Then the decision's violations are reported, each naming the artifact, the place in it and the rule broken
    And they come in the order the places stand in the decision as it reads back: the field first, then the sections, then the options
    And the two violations at the field come in the alphabetical order of the names of the rules they break

  @slice-164
  Scenario: An artifact that conforms to a version of its type a later version has followed is listed as behind its type
    Pins that falling behind a type is news, not damage: it is listed on its own so nobody has to fix it before the store can be trusted.
    Given a store holding a decision that conforms to the first version of the decision type
    And a second version of the decision type has followed it
    When the client checks the store
    Then that decision is listed as behind its type
    And it is not reported as a violation

  @slice-164
  Scenario Outline: An artifact behind its type is checked against the version of its type it conforms to
    Pins that an artifact is judged by the version it conforms to, never by a later one, so whether it is wrong does not depend on how far its type has moved on.
    Given a store holding a decision that conforms to the first version of the decision type
    And a second version of the decision type has followed it
    And the decision <how it fits>
    When the client checks the store
    Then that decision is listed as behind its type
    And it <is it a violation>

    Examples:
      | how it fits                               | is it a violation                                                                     |
      | fits the first version but not the second | is not reported as a violation                                                        |
      | does not fit the first version            | is reported as a violation, naming the artifact, the place in it and the rule broken |

  @slice-170
  Scenario: A store holding links to IRIs it does not hold lists each placeholder with what links to it
    Pins that a link to something the store does not hold is reported as a placeholder with every link into it, so each can be found and filled, and never mixed in with what is wrong or what is behind.
    Given a store holding a decision that links to an IRI the store does not hold from one of its fields and again from one of its items
    And the store holds another decision that breaks a rule of its type
    And the store holds a third decision that conforms to a version of the decision type a later version has followed
    When the client checks the store
    Then the IRI is listed as a placeholder with each link into it: the decision and the field, and the decision and the item
    And the placeholder is listed apart from the violations and from the artifacts behind their type

  @slice-170
  Scenario: A store whose only findings are placeholders reports no violation
    Pins that a placeholder is never damage: a store whose links reach only things it does not hold still checks clean.
    Given a store where everything fits its type and one decision links to an IRI the store does not hold
    When the client checks the store
    Then the client is told of no violation
    And the IRI is listed as a placeholder
