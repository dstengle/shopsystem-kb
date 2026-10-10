# formulated from spec/capabilities/check-a-change.md
Feature: Check a change
  Narrator: the client

  Scenario: An artifact created naming a version of its type is checked against that version
    Pins that a create is held to the version it names, not to the latest one, so a client can write to the version it knows.
    Given a store holding two versions of the decision type, where the later one requires a section the earlier one does not
    When the client creates a decision naming the earlier version of the decision type, with content that fits the earlier version and lacks the section the later one requires, saying which role and why
    Then the client is given the IRI the artifact keeps for life and its first version

  @slice-25
  Scenario: An artifact missing a required section is refused
    Pins that the sections a type requires are checked at creation, in order, so nothing incomplete gets into the store to be fixed later.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision with a rationale and no purpose, saying which role and why
    Then the artifact is rejected because the sections the type requires must all be present, in order

  Scenario: An artifact pointing at an IRI under a type the store does not hold is refused
    Pins that a link may only reach toward a type the store knows, so nothing in the graph points into a kind nobody has defined.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision that supersedes an IRI under a type the store does not hold, saying which role and why
    Then the artifact is rejected because a link must land on a node of a kind the type allows

  Scenario: An artifact pointing at an IRI the store does not hold, under a type it holds that the link allows, lands its link on a placeholder
    Pins that a link may run ahead of what it points at, so a client can write what it knows before the rest is written.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision that supersedes a decision the store does not hold, at an IRI under the decision type, saying which role and why
    Then the client is given the IRI the artifact keeps for life and its first version
    And asked for the placeholders, the client is given that IRI, with the new decision linking to it

  Scenario: An artifact pointing into a part of an IRI the store does not hold, under a type it holds that the link allows, lands its link on a placeholder
    Pins that a link into a part may run ahead of the artifact that will hold the part, as a link to a whole artifact may.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede or into one of its options, and may carry a collection of options
    When the client creates a decision that supersedes an option of a decision the store does not hold, at an IRI under the decision type, saying which role and why
    Then the client is given the IRI the artifact keeps for life and its first version
    And asked for the placeholders, the client is given the IRI the link points at, with the new decision linking to it

  Scenario: An artifact pointing into a part a held artifact does not have is refused
    Pins that a placeholder stands only for what is not held, so a link into a held artifact must find the part it names.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede or into one of its options, and may carry a collection of options
    And a decision the store holds, with no option named "rollback"
    When the client creates a decision that supersedes the option "rollback" of that decision, saying which role and why
    Then the artifact is rejected because a link must land on a node of a kind the type allows

  Scenario: An artifact pointing at an IRI the store does not hold, under a type the link does not allow, is refused
    Pins that a placeholder is typed by the IRI it sits under, so a link to something not yet written is held to the link's kinds as a link to something held is.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    And a process type
    When the client creates a decision that supersedes an IRI the store does not hold, under the process type, saying which role and why
    Then the artifact is rejected because a link must land on a node of a kind the type allows

  Scenario: Creating an artifact at an IRI links already point at fills the placeholder
    Pins that a placeholder is filled by creating what it names, with no relinking by the client.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    And a decision that supersedes a decision the store does not hold, at an IRI under the decision type
    When the client creates a decision at that IRI, saying which role and why
    Then following the link from the first decision reaches the new decision
    And asked for the placeholders, the client is not given that IRI

  Scenario: Creating an artifact without the part a link points into leaves that link on a placeholder
    Pins that creating the artifact fills only what it holds, so a link into a part it lacks is reported, not refused and not lost.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede or into one of its options, and may carry a collection of options
    And a decision that supersedes the option "rollback" of a decision the store does not hold, at an IRI under the decision type
    When the client creates a decision at that IRI with no option named "rollback", saying which role and why
    Then the client is given the IRI the artifact keeps for life and its first version
    And asked for the placeholders, the client is given the IRI the link points at, with the first decision linking to it

  Scenario: An artifact with several faults reports them all
    Pins that a refusal is a full account rather than the first complaint, so a client can fix everything in one more attempt and the store is untouched meanwhile.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision that is missing its purpose and supersedes an IRI under a type the store does not hold, saying which role and why
    Then the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken
    And the store is unchanged

  @slice-73
  Scenario: Faults found by different rules all come back together
    Pins that a refusal is one full account however the faults were found, so a client never fixes what the shape of the content says only to be told about a missing section next time.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision whose options are of a shape the type does not allow and which is also missing its purpose, saying which role and why
    Then the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken
    And the store is unchanged

  @slice-126
  Scenario: An artifact refused with several faults has them given in the order its places stand when it reads back
    Pins that a refusal reads in the order the artifact would read back, not the order the client wrote it in, and that faults at one place are told apart by a fixed order of their rules, so a client can compare refusals from one attempt to the next.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    And the decision type declares its fields first, then its required sections, then its collection of options
    When the client creates a decision written with its options first, then its sections, then its fields, where a field breaks two rules of the type, the second option is of a shape the type does not allow, and the rationale is missing, saying which role and why
    Then the artifact is rejected with every fault, each naming the artifact, the place in it and the rule broken
    And the faults come in the order the places stand in the decision as it would read back: the field first, then the sections, then the options
    And the two faults at the field come in the alphabetical order of the names of the rules they break
    And the store is unchanged

  @slice-1.6
  Scenario: A section carrying anything besides its title, its body and its own sections is refused
    Pins the shape of a section exactly, so prose stays prose and nobody starts keeping domain data in the margins of it.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision whose purpose carries an extra entry of its own besides its title, its body and the sections inside it, saying which role and why
    Then the artifact is rejected because a section holds exactly its title, its body and the sections inside it, and the extra entry is named

  @slice-1.13
  Scenario: A section with no title is refused
    Pins that both halves of a section are required, and that a missing one is an ordinary failure to fit the type rather than a special case.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision whose first section carries a body and no title, saying which role and why
    Then the artifact is rejected because a section carries both a title and a body, and a section without one does not fit its type like anything else that does not

  @slice-1.13
  Scenario: A section with no body is refused
    Pins the other half: a body may be empty, but it may not be left out, so every section has somewhere for its prose to go.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision whose purpose carries a title and no body, saying which role and why
    Then the artifact is rejected because a section carries both a title and a body, and a section without one does not fit its type like anything else that does not

  @slice-92
  Scenario: A section whose body is empty is kept as it is
    Pins that an empty body is content and not an omission, so a client can write a heading before it has the prose and read it back the way it wrote it.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision whose rationale carries a title and an empty body, saying which role and why
    Then the client is given the name the artifact keeps for life and its first version
    And the rationale reads back with an empty body

  Scenario: Changing an artifact that is behind its type naming no version keeps it at the version it conforms to
    Pins that a change naming no version never moves an artifact to a later version of its type, so being behind is cleared only by asking for it.
    Given a store holding a decision with a purpose and a rationale, at its first version
    Given a decision last checked against an older version of the decision type, where the current version requires a section the older one does not
    When the client replaces the decision naming no version, with content that fits the older version and lacks the section the current one requires, saying which role and why
    Then the decision is replaced
    And it is still listed as behind its type

  Scenario: Changing an artifact that is behind its type naming the latest version, with content that fits it, brings it up to date
    Pins that an artifact moves to the latest version of its type when a change names it and fits it, and that this clears being behind.
    Given a store holding a decision with a purpose and a rationale, at its first version
    Given a decision last checked against an older version of the decision type
    When the client replaces the decision naming the latest version of the decision type, with content that fits that version, saying which role and why
    Then the decision records the latest version of its type
    And it is no longer listed as behind its type

  Scenario: Changing an artifact that is behind its type naming a later version, with content that does not fit it, is refused
    Pins that naming a later version buys no leniency: the change is checked against the version it names, and a refused one changes nothing, being behind included.
    Given a store holding a decision with a purpose and a rationale, at its first version
    Given a decision last checked against an older version of the decision type
    When the client replaces the decision naming the latest version of the decision type, with content that does not fit that version, saying which role and why
    Then the change is rejected because the content does not fit the version it names, like any change that does not fit
    And reading the decision gives what it held before, at the version it held before
    And it is still listed as behind its type

  @slice-8
  Scenario: A change that would break the type leaves the artifact as it was
    Pins check-then-swap: a change is applied to a copy and only lands if it passes, so a refused change is never visible afterwards.
    Given a store holding a decision with a purpose and a rationale, at its first version
    When the client replaces the decision with content that has no purpose, saying which role and why
    Then the change is rejected because the sections the type requires must all be present, in order
    And reading the decision gives what it held before, at the version it held before

  Scenario: An item pointing at an IRI under a type the store does not hold is refused
    Pins that a link inside an item is held to the types the store knows like any other link, so nothing reaches into an undefined kind by sitting inside a collection.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step that points at an IRI under a type the store does not hold, saying which role and why
    Then the item is rejected because a link must land on a node of a kind the type allows
    And the process holds the steps it held before, at the version it held before

  @slice-66
  Scenario: An item missing something its own type requires is refused
    Pins that an item is checked against its type the way an artifact is checked against its, so a collection cannot fill up with half-filled items nobody checked.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step with no role named, where a step must name a role, saying which role and why
    Then the item is rejected because the content does not fit the type
    And the process holds the steps it held before, at the version it held before
