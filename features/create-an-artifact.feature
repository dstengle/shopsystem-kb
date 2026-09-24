Feature: Create an artifact
So that a client can put content into the store and get a name it can come back to, the client can create an artifact.

  Background:
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options

  @slice-1
  Scenario: The client creates an artifact
    When the client creates a decision with a title, both required sections and two options, saying which role and why
    Then the client is given the name the artifact keeps for life and its first version
    And the artifact records the version of the type it was checked against
    And reading it back gives what was written, in the order the type declares

  @slice-24
  Scenario: The name of a new artifact is made from its title, not asked for
    When the client creates a decision titled "Price reviews happen weekly", saying which role and why
    Then the name the client is given is made from that title
    And the client never said what the name should be

  @slice-24
  Scenario: A second artifact with a title already used gets a name of its own
    Given a decision the store already holds, titled "Price reviews happen weekly"
    When the client creates another decision with that same title, saying which role and why
    Then the client is given a name of its own for the new decision, the name already taken with a number added
    And the decision created first keeps the name it had

  @slice-24
  Scenario: Two parts with the same title are given names of their own
    When the client creates a decision carrying two options with the same title, saying which role and why
    Then each option is given a name of its own, the second the name of the first with a number added
    And the client never said what either name should be

  @slice-24
  Scenario: An artifact missing a required section is refused
    When the client creates a decision with a rationale and no purpose, saying which role and why
    Then the artifact is rejected because the sections the type requires must all be present, in order

  @slice-24
  Scenario: An artifact pointing at something that is not there is refused
    When the client creates a decision that supersedes a decision the store does not hold, saying which role and why
    Then the artifact is rejected because a link must land on a node of a kind the type allows

  @slice-7
  Scenario: An artifact with several faults reports them all
    When the client creates a decision that is missing its purpose and supersedes a decision the store does not hold, saying which role and why
    Then the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken
    And the store is unchanged

  @slice-59
  Scenario: An artifact created without a title is refused
    When the client creates a decision with both required sections and no title, saying which role and why
    Then the artifact is rejected because an artifact cannot be created without a title

  @slice-59
  Scenario: Content that settles what only the store settles is refused
    When the client creates a decision whose content carries a name and a version for the artifact itself, saying which role and why
    Then the artifact is rejected because content holds only what the type declares, and each thing it carried that only the store settles is named back

  @slice-55
  Scenario: Content carrying a title of its own is refused
    When the client creates a decision whose content carries a title as well as the title given alongside it, saying which role and why
    Then the artifact is rejected because a title is given alongside the content, never inside it, and the title the content carried is named back

  @slice-59
  Scenario: A title with capitals and punctuation gives a plain name
    When the client creates a decision titled "Price reviews: weekly, from now on!", saying which role and why
    Then the name the client is given is that title in lower case, with each run of anything that is not a letter or a digit turned into a single hyphen, and no hyphen at either end

  @slice-59
  Scenario: A title that leaves nothing to make a name from is refused
    When the client creates a decision titled "!!!", saying which role and why
    Then the artifact is rejected because a title must leave something to make a name from

  @slice-58
  Scenario: A title that reads as a date is still a title
    When the client creates a decision titled "2026-09-24", saying which role and why
    Then the title reads back as the text that was written, not as a date
    And the name the client is given is made from that text

  @slice-59
  Scenario: A title that reads as yes is still a title
    When the client creates a decision titled "yes", saying which role and why
    Then the title reads back as the text that was written, not as a yes or a no
    And the name the client is given is made from that text

  @slice-59
  Scenario: Content telling the store how to build a value is refused
    When the client creates a decision whose content carries a tag on one of its values, saying which role and why
    Then the artifact is rejected because content is read plainly as written and carries no tags

  @slice-59
  Scenario: Content holding more than one document is refused
    When the client creates a decision from content holding two documents one after the other, saying which role and why
    Then the artifact is rejected because content holds exactly one document

  @slice-59
  Scenario: A section carrying anything besides its title, its body and its own sections is refused
    When the client creates a decision whose purpose carries an extra entry of its own besides its title, its body and the sections inside it, saying which role and why
    Then the artifact is rejected because a section holds exactly its title, its body and the sections inside it, and the extra entry is named

  Scenario: A section with no title is refused
    When the client creates a decision whose first section carries a body and no title, saying which role and why
    Then the artifact is rejected because a section carries both a title and a body, and a section without one does not fit its type like anything else that does not

  Scenario: A section with no body is refused
    When the client creates a decision whose purpose carries a title and no body, saying which role and why
    Then the artifact is rejected because a section carries both a title and a body, and a section without one does not fit its type like anything else that does not

  Scenario: A value that reads as a switch or as a clock time is still the text that was written
    When the client creates a decision carrying one field written "on" and another written "1:20", saying which role and why
    Then both fields read back as the text that was written, the first not as a yes or a no and the second not as a number

  Scenario: Content that writes a value once and points back at it elsewhere is refused
    When the client creates a decision whose content writes a value once and points back at it from another place instead of writing it again, saying which role and why
    Then the artifact is rejected because content is read exactly as written and nothing in it stands in for a value written somewhere else

  Scenario: A kind that is not a plain name is refused
    When the client creates an artifact of the kind "../schema/decision", with a title and both required sections, saying which role and why
    Then the artifact is rejected because a kind is a plain name of lower-case letters, digits and single hyphens, never a path
    And nothing is looked up or written anywhere, inside the store or outside it
