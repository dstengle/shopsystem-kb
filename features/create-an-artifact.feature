Feature: Create an artifact
So that a client can put content into the store and get a name it can come back to, the client can create an artifact.

  Background:
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options

  @slice-1
  Scenario: The client creates an artifact
    Pins the walking skeleton's write: a create goes through checking to disk and comes back as a name the client can use, with the content reading back in the order the type declares.
    When the client creates a decision with a title, both required sections and two options, saying which role and why
    Then the client is given the name the artifact keeps for life and its first version
    And the artifact records the version of the type it was checked against
    And reading it back gives what was written, in the order the type declares

  @slice-25
  Scenario: The name of a new artifact is made from its title, not asked for
    Pins that names are minted by the store from the title, so a client cannot choose one and never has to invent one.
    When the client creates a decision titled "Price reviews happen weekly", saying which role and why
    Then the name the client is given is made from that title
    And the client never said what the name should be

  @slice-8.1
  Scenario: A second artifact with a title already used gets a name of its own
    Pins how a clash is settled: the newcomer takes a numbered name and the artifact already there keeps the name everything else points at.
    Given a decision the store already holds, titled "Price reviews happen weekly"
    When the client creates another decision with that same title, saying which role and why
    Then the client is given a name of its own for the new decision, the name already taken with a number added
    And the decision created first keeps the name it had

  @slice-25
  Scenario: Two parts with the same title are given names of their own
    Pins that parts are named by the same rules as artifacts, including the clash rule, so every part inside a new artifact is addressable from the moment it exists.
    When the client creates a decision carrying two options with the same title, saying which role and why
    Then each option is given a name of its own, the second the name of the first with a number added
    And the client never said what either name should be

  @slice-25
  Scenario: An artifact missing a required section is refused
    Pins that the sections a type requires are checked at creation, in order, so nothing incomplete gets into the store to be fixed later.
    When the client creates a decision with a rationale and no purpose, saying which role and why
    Then the artifact is rejected because the sections the type requires must all be present, in order

  @slice-25
  Scenario: An artifact pointing at something that is not there is refused
    Pins that links are checked against the store as it stands, so the graph never contains a link that lands nowhere.
    When the client creates a decision that supersedes a decision the store does not hold, saying which role and why
    Then the artifact is rejected because a link must land on a node of a kind the type allows

  @slice-7
  Scenario: An artifact with several faults reports them all
    Pins that a refusal is a full account rather than the first complaint, so a client can fix everything in one more attempt and the store is untouched meanwhile.
    When the client creates a decision that is missing its purpose and supersedes a decision the store does not hold, saying which role and why
    Then the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken
    And the store is unchanged

  @slice-1.6
  Scenario: An artifact created without a title is refused
    Pins that a title is not optional, because the store has nothing to make a name from without one.
    When the client creates a decision with both required sections and no title, saying which role and why
    Then the artifact is rejected because an artifact cannot be created without a title

  @slice-1.6
  Scenario: Content that settles what only the store settles is refused
    Pins the boundary around identity: name and version belong to the store alone, and content reaching for either is refused with each such entry named back.
    When the client creates a decision whose content carries a name and a version for the artifact itself, saying which role and why
    Then the artifact is rejected because content holds only what the type declares, and each thing it carried that only the store settles is named back

  @slice-1.2
  Scenario: Content carrying a title of its own is refused
    Pins that a title travels beside the content and never inside it, so there is never a second title to choose between.
    When the client creates a decision whose content carries a title as well as the title given alongside it, saying which role and why
    Then the artifact is rejected because a title is given alongside the content, never inside it, and the title the content carried is named back

  @slice-1.6
  Scenario: A title with capitals and punctuation gives a plain name
    Pins exactly how a title becomes a name, so the same title always gives the same name and every name is safe to put in a path or a link.
    When the client creates a decision titled "Price reviews: weekly, from now on!", saying which role and why
    Then the name the client is given is that title in lower case, with each run of anything that is not a letter or a digit turned into a single hyphen, and no hyphen at either end

  @slice-1.6
  Scenario: A title that leaves nothing to make a name from is refused
    Pins the edge of that rule: rather than invent a name when the title boils down to nothing, the store refuses and says why.
    When the client creates a decision titled "!!!", saying which role and why
    Then the artifact is rejected because a title must leave something to make a name from

  @slice-1.5
  Scenario: A title that reads as a date is still a title
    Pins that a title is always text: nothing quietly reads it as a date on the way in and hands back something the client never wrote.
    When the client creates a decision titled "2026-09-24", saying which role and why
    Then the title reads back as the text that was written, not as a date
    And the name the client is given is made from that text

  @slice-1.6
  Scenario: A title that reads as yes is still a title
    Pins the same for the words older readers turn into yes and no, which is the classic way a title comes back as something else entirely.
    When the client creates a decision titled "yes", saying which role and why
    Then the title reads back as the text that was written, not as a yes or a no
    And the name the client is given is made from that text

  @slice-1.6
  Scenario: Content telling the store how to build a value is refused
    Pins that content is data and nothing more: it cannot instruct the store how to construct a value, which is where reading untrusted content turns dangerous.
    When the client creates a decision whose content carries a tag on one of its values, saying which role and why
    Then the artifact is rejected because content is read plainly as written and carries no tags

  @slice-1.6
  Scenario: Content holding more than one document is refused
    Pins that one create means one document, so nothing extra can ride along unnoticed behind the part that was checked.
    When the client creates a decision from content holding two documents one after the other, saying which role and why
    Then the artifact is rejected because content holds exactly one document

  @slice-1.6
  Scenario: A section carrying anything besides its title, its body and its own sections is refused
    Pins the shape of a section exactly, so prose stays prose and nobody starts keeping domain data in the margins of it.
    When the client creates a decision whose purpose carries an extra entry of its own besides its title, its body and the sections inside it, saying which role and why
    Then the artifact is rejected because a section holds exactly its title, its body and the sections inside it, and the extra entry is named

  @slice-1.13
  Scenario: A section with no title is refused
    Pins that both halves of a section are required, and that a missing one is an ordinary failure to fit the type rather than a special case.
    When the client creates a decision whose first section carries a body and no title, saying which role and why
    Then the artifact is rejected because a section carries both a title and a body, and a section without one does not fit its type like anything else that does not

  @slice-1.13
  Scenario: A section with no body is refused
    Pins the other half: a body may be empty, but it may not be left out, so every section has somewhere for its prose to go.
    When the client creates a decision whose purpose carries a title and no body, saying which role and why
    Then the artifact is rejected because a section carries both a title and a body, and a section without one does not fit its type like anything else that does not

  @slice-1.11
  Scenario: A value that reads as a switch or as a clock time is still the text that was written
    Pins that the store reads content by the modern rules throughout, so the old traps of on-meaning-yes and a clock time becoming a number cannot bite a client's data.
    When the client creates a decision carrying one field written "on" and another written "1:20", saying which role and why
    Then both fields read back as the text that was written, the first not as a yes or a no and the second not as a number

  @slice-1.12
  Scenario: Content that writes a value once and points back at it elsewhere is refused
    Pins that content means only what it says on the page: nothing in it expands into something written elsewhere, which keeps reading it cheap and safe.
    When the client creates a decision whose content writes a value once and points back at it from another place instead of writing it again, saying which role and why
    Then the artifact is rejected because content is read exactly as written and nothing in it stands in for a value written somewhere else

  @slice-1.14
  Scenario: A kind that is not a plain name is refused
    Pins that the kind is checked for shape before anything is looked up or worked out from it, so a kind shaped like a path never reaches the disk.
    When the client creates an artifact of the kind "../schema/decision", with a title and both required sections, saying which role and why
    Then the artifact is rejected because a kind is a plain name of lower-case letters, digits and single hyphens, never a path
    And nothing is looked up or written anywhere, inside the store or outside it

  @slice-1.25
  Scenario: A kind the store holds no type for is refused
    Pins that an unknown kind is its own plain answer, named back and kept apart from any complaint about the content, so a client can tell a typo from a bad artifact.
    Given a store that holds no type called "invoice"
    When the client creates an artifact of the kind "invoice", with a title and both required sections, saying which role and why
    Then the artifact is rejected because a kind must name a type the store holds, and the kind asked for is given back
    And that fault stands on its own, apart from anything wrong with the content
    And nothing is written anywhere in the store

  @slice-1.22
  Scenario: Content that opens by declaring the format it is written in is refused
    Pins that content cannot choose the rules it is read by: the store reads everything the one way, and an attempt to declare otherwise is refused with the spot named.
    Given content for a decision that opens with a line declaring which version of the writing format the rest is in
    When the client creates a decision from that content, saying which role and why
    Then the artifact is rejected because content is read plainly as written and opens with no declaration of its format, and the place the declaration stands is named

  @slice-1.21
  Scenario: Content naming the same entry twice is refused
    Pins that a repeated entry is refused rather than silently resolved, since whichever one a reader kept would be a guess at what the client meant.
    Given content for a decision that names the same entry twice in the same place
    When the client creates a decision from that content, saying which role and why
    Then the artifact is rejected because an entry is named once and only once, and the place the second one stands is named

  @slice-1.25
  Scenario: Values written as a yes-or-no, as nothing and as a number keep those meanings
    Pins the other side of reading content plainly: what is genuinely a yes-or-no, a nothing or a number stays one, so the rule is precise rather than turning everything into text.
    Given content for a decision carrying one field written "true", one field left as nothing, and one field written "12.5"
    When the client creates a decision from that content, saying which role and why
    Then the first field reads back as a yes-or-no, the second as nothing at all, and the third as a number
    And none of the three reads back as text

  @slice-1.18
  Scenario: A title given as a yes-or-no is still a title
    Pins that a title is turned into text whatever arrives, so a client that sends an unquoted word still gets a title and a name it can use.
    Given a title for a new decision that is the yes-or-no true rather than text
    When the client creates a decision with that title, saying which role and why
    Then the title reads back as the text "true"
    And the name the client is given is made from that text

  @slice-1.25
  Scenario: A title given as a number is still a title
    Pins the same for a number, which is how a title like a year or a version arrives when nobody quoted it.
    Given a title for a new decision that is the number 12 rather than text
    When the client creates a decision with that title, saying which role and why
    Then the title reads back as the text "12"
    And the name the client is given is made from that text

  @slice-75
  Scenario Outline: Content the store cannot make sense of is refused
    Pins that every shape of content the store cannot take is a named refusal rather than a call that breaks off, so a client is never handed a crash in place of an answer.
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

  @slice-73
  Scenario: Faults found by different rules all come back together
    Pins that a refusal is one full account however the faults were found, so a client never fixes what the shape of the content says only to be told about a missing section next time.
    When the client creates a decision whose options are of a shape the type does not allow and which is also missing its purpose, saying which role and why
    Then the artifact is rejected with both faults, each naming the artifact, the place in it and the rule broken
    And the store is unchanged

  @slice-78
  Scenario: A field written as a bare date is the text that was written
    Pins the last of the reading traps: a date written without quotes is text like anything else, so a field the type declares as text is not refused for looking like a day.
    When the client creates a decision carrying a field written "2026-09-24", saying which role and why
    Then that field reads back as the text that was written, not as a date

  @slice-92
  Scenario: A section whose body is empty is kept as it is
    Pins that an empty body is content and not an omission, so a client can write a heading before it has the prose and read it back the way it wrote it.
    When the client creates a decision whose rationale carries a title and an empty body, saying which role and why
    Then the client is given the name the artifact keeps for life and its first version
    And the rationale reads back with an empty body

  @slice-92
  Scenario: Prose the store could not write back in its one form is refused
    Pins that the store checks its own output as strictly as its input: prose it could not lay down the way it lays down all prose is refused, rather than written some other way.
    When the client creates a decision one of whose lines of prose ends in a space, saying which role and why
    Then the artifact is rejected because every piece of prose is written as a block, and this prose could not be written back as one
    And nothing is written anywhere in the store
