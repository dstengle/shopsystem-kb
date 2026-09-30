# formulated from spec/capabilities/hand-over-content.md
Feature: Hand over content
  Narrator: the client

  @slice-1.6
  Scenario: Content that settles what only the store settles is refused
    Pins the boundary around identity: name and version belong to the store alone, and content reaching for either is refused with each such entry named back.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision whose content carries a name and a version for the artifact itself, saying which role and why
    Then the artifact is rejected because content holds only what the type declares, and each thing it carried that only the store settles is named back

  @slice-1.2
  Scenario: Content carrying a title of its own is refused
    Pins that a title travels beside the content and never inside it, so there is never a second title to choose between.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision whose content carries a title as well as the title given alongside it, saying which role and why
    Then the artifact is rejected because a title is given alongside the content, never inside it, and the title the content carried is named back

  @slice-23
  Scenario: A change whose content settles what only the store settles is refused
    Pins that identity stays the store's business on a change as much as on a create: content cannot set its own version, and the offending entry is named back.
    Given a store holding a decision with a purpose and a rationale, at its first version
    When the client replaces the decision with content carrying a version of its own, saying which role and why
    Then the change is rejected because content holds only what the type declares, and the thing it carried that only the store settles is named back
    And reading the decision gives what it held before, at the version it held before

  @slice-39
  Scenario: An item whose content settles what only the store settles is refused
    Pins that content carries only what the type declares here too: an item cannot smuggle in its own identity, and the refusal leaves the collection as it was.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step whose content carries a name of its own, saying which role and why
    Then the item is rejected because content holds only what the type declares, and the thing it carried that only the store settles is named back
    And the process holds the steps it held before, at the version it held before

  @slice-1.6
  Scenario: Content telling the store how to build a value is refused
    Pins that content is data and nothing more: it cannot instruct the store how to construct a value, which is where reading untrusted content turns dangerous.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision whose content carries a tag on one of its values, saying which role and why
    Then the artifact is rejected because content is read plainly as written and carries no tags

  @slice-1.6
  Scenario: Content holding more than one document is refused
    Pins that one create means one document, so nothing extra can ride along unnoticed behind the part that was checked.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision from content holding two documents one after the other, saying which role and why
    Then the artifact is rejected because content holds exactly one document

  @slice-1.11
  Scenario: A value that reads as a switch or as a clock time is still the text that was written
    Pins that the store reads content by the modern rules throughout, so the old traps of on-meaning-yes and a clock time becoming a number cannot bite a client's data.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision carrying one field written "on" and another written "1:20", saying which role and why
    Then both fields read back as the text that was written, the first not as a yes or a no and the second not as a number

  @slice-1.12
  Scenario: Content that writes a value once and points back at it elsewhere is refused
    Pins that content means only what it says on the page: nothing in it expands into something written elsewhere, which keeps reading it cheap and safe.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision whose content writes a value once and points back at it from another place instead of writing it again, saying which role and why
    Then the artifact is rejected because content is read exactly as written and nothing in it stands in for a value written somewhere else

  @slice-1.22
  Scenario: Content that opens by declaring the format it is written in is refused
    Pins that content cannot choose the rules it is read by: the store reads everything the one way, and an attempt to declare otherwise is refused with the spot named.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    Given content for a decision that opens with a line declaring which version of the writing format the rest is in
    When the client creates a decision from that content, saying which role and why
    Then the artifact is rejected because content is read plainly as written and opens with no declaration of its format, and the place the declaration stands is named

  @slice-1.21
  Scenario: Content naming the same entry twice is refused
    Pins that a repeated entry is refused rather than silently resolved, since whichever one a reader kept would be a guess at what the client meant.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    Given content for a decision that names the same entry twice in the same place
    When the client creates a decision from that content, saying which role and why
    Then the artifact is rejected because an entry is named once and only once, and the place the second one stands is named

  @slice-1.25
  Scenario: Values written as a yes-or-no, as nothing and as a number keep those meanings
    Pins the other side of reading content plainly: what is genuinely a yes-or-no, a nothing or a number stays one, so the rule is precise rather than turning everything into text.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    Given content for a decision carrying one field written "true", one field left as nothing, and one field written "12.5"
    When the client creates a decision from that content, saying which role and why
    Then the first field reads back as a yes-or-no, the second as nothing at all, and the third as a number
    And none of the three reads back as text

  @slice-75
  Scenario Outline: Content the store cannot make sense of is refused
    Pins that every shape of content the store cannot take is a named refusal rather than a call that breaks off, so a client is never handed a crash in place of an answer.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision from <content>, saying which role and why
    Then the artifact is rejected because <reason>, and the place it went wrong is named
    And the call comes back with its answer rather than breaking off
    And nothing is written anywhere in the store

    Examples:
      | content                                                        | reason                              |
      | content that cannot be read as written at all                  | content cannot be read as written   |
      | content that is a list rather than a set of named entries      | content is a set of named entries   |
      | content that is a single bare value                            | content is a set of named entries   |
      | content with nothing in it at all                              | content is a set of named entries   |
      | content whose sections are one line of text rather than sections | the content does not fit the type |
      | content whose options are a single value rather than a collection | the content does not fit the type |
      | content one of whose options is a bare value                   | the content does not fit the type   |

  @slice-78
  Scenario: A field written as a bare date is the text that was written
    Pins the last of the reading traps: a date written without quotes is text like anything else, so a field the type declares as text is not refused for looking like a day.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision carrying a field written "2026-09-24", saying which role and why
    Then that field reads back as the text that was written, not as a date

  @slice-92
  Scenario: Prose the store could not write back in its one form is refused
    Pins that the store checks its own output as strictly as its input: prose it could not lay down the way it lays down all prose is refused, rather than written some other way.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision one of whose lines of prose ends in a space, saying which role and why
    Then the artifact is rejected because every piece of prose is written as a block, and this prose could not be written back as one
    And nothing is written anywhere in the store
