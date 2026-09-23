Feature: Create an artifact
So that a client can put content into the store and get a name it can come back to, the client can create an artifact.

  Background:
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options

  @assumes-artifacts-are-typed-ordered-documents
  Scenario: The client creates an artifact
    When the client creates a decision with a title, both required sections and two options, saying which role and why
    Then the client is given the name the artifact keeps for life and its first version
    And the artifact records the version of the type it was checked against
    And reading it back gives what was written, in the order the type declares

  @assumes-parts-are-nodes-not-quoted-text
  Scenario: Each part of a new artifact stands on its own
    When the client creates a decision carrying two options, saying which role and why
    Then each option has a name unique among the options
    And the client can read or change one option without touching the other

  @assumes-artifacts-are-typed-ordered-documents
  Scenario: An artifact may add sections of its own after the ones its type requires
    When the client creates a decision with the two required sections followed by a section of its own, saying which role and why
    Then the artifact is accepted
    And its own section comes after the required ones

  @assumes-every-change-is-validated-before-it-is-written
  Scenario: An artifact missing a required section is refused
    When the client creates a decision with a rationale and no purpose, saying which role and why
    Then the artifact is rejected because the sections the type requires must all be present, in order

  @assumes-references-are-part-of-the-type
  Scenario: An artifact pointing at something that is not there is refused
    When the client creates a decision that supersedes a decision the store does not hold, saying which role and why
    Then the artifact is rejected because a link must land on a node of a kind the type allows

  @assumes-parts-are-nodes-not-quoted-text
  Scenario: An artifact with two parts of the same name is refused
    When the client creates a decision carrying two options of the same name, saying which role and why
    Then the artifact is rejected because part names must be unique within their collection

  @assumes-all-faults-come-back-not-the-first
  Scenario: An artifact with several faults reports them all
    When the client creates a decision that is missing its purpose and supersedes a decision the store does not hold, saying which role and why
    Then the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken
    And the store is unchanged
