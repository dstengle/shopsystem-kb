# formulated from spec/capabilities/name-artifacts-and-items.md
Feature: Name artifacts and items
  Narrator: the client

  Scenario: An artifact created at an IRI of the client's choosing under its type's IRI is held at that IRI
    Pins that the client names every artifact it creates and the store keeps the name it was given, never one of its own.
    Given a store holding a decision type at "https://shop.example/kb/decision"
    When the client creates a decision at "https://shop.example/kb/decision/pricing/weekly-reviews", saying which role and why
    Then the decision is held at "https://shop.example/kb/decision/pricing/weekly-reviews"
    And the store made up no other IRI for it

  Scenario: An artifact created at an IRI not under its type's IRI is refused
    Pins that where an artifact is named says what kind it is, so an IRI outside its type's is never held.
    Given a store holding a decision type at "https://shop.example/kb/decision"
    When the client creates a decision at "https://shop.example/kb/process/weekly-reviews", saying which role and why
    Then the artifact is rejected because an artifact's IRI sits under its type's IRI
    And the refusal names "https://shop.example/kb/process/weekly-reviews"
    And nothing is written

  Scenario: An artifact created at an IRI the store already holds an artifact at is refused
    Pins that an IRI names one artifact: a second create there is refused rather than numbered or put over the first.
    Given a store holding a decision type at "https://shop.example/kb/decision"
    Given a decision the store holds at "https://shop.example/kb/decision/weekly-reviews"
    When the client creates another decision at "https://shop.example/kb/decision/weekly-reviews", saying which role and why
    Then the artifact is rejected because an IRI names one artifact
    And the refusal names "https://shop.example/kb/decision/weekly-reviews"
    And the decision already there reads as it did, at the revision it held

  Scenario: An artifact keeps the IRI it was created with for life
    Pins that changing an artifact never moves it, so anything pointing at its IRI still finds it.
    Given a store holding a decision type at "https://shop.example/kb/decision"
    Given a decision the store holds at "https://shop.example/kb/decision/weekly-reviews", changed several times since it was created
    When the client reads the decision at "https://shop.example/kb/decision/weekly-reviews"
    Then the client is given the decision, at its latest revision

  Scenario: Two items created with the same title in one collection, neither given a name, are given names of their own
    Pins the clash rule for parts the store names on create: neither is left unnamed, and the second takes the first's name with a number added.
    Given a store holding a decision type at "https://shop.example/kb/decision" whose decisions may carry a collection of options
    When the client creates a decision carrying two options with the same title, neither given a name, saying which role and why
    Then each option is given a name of its own, the second the name of the first with a number added

  Scenario: An item's title with capitals and punctuation gives a plain name
    Pins exactly how an item's title becomes its name, so the same title always gives the same name and every name is safe to put in an IRI.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step titled "Count stock: shelf, then back room!" to the process, saying which role and why
    Then the name the client is given for the new item is that title in lower case, with each run of anything that is not a letter or a digit turned into a single hyphen, and no hyphen at either end

  Scenario: A title that reads as a date is still a title
    Pins that a title is always text: nothing quietly reads it as a date on the way in and hands back something the client never wrote.
    Given a store holding a decision type at "https://shop.example/kb/decision"
    When the client creates a decision titled "2026-09-24", saying which role and why
    Then the title reads back as the text that was written, not as a date

  Scenario: A title that reads as yes is still a title
    Pins the same for the words older readers turn into yes and no, which is the classic way a title comes back as something else entirely.
    Given a store holding a decision type at "https://shop.example/kb/decision"
    When the client creates a decision titled "yes", saying which role and why
    Then the title reads back as the text that was written, not as a yes or a no

  Scenario: A title given as the yes-or-no true is still a title
    Pins that a title is turned into text whatever arrives, so a client that sends an unquoted word still gets a title it can use.
    Given a store holding a decision type at "https://shop.example/kb/decision"
    Given a title for a new decision that is the yes-or-no true rather than text
    When the client creates a decision with that title, saying which role and why
    Then the title reads back as the text "true"

  Scenario: A title given as the number 12 is still a title
    Pins the same for a number, which is how a title like a year or a version arrives when nobody quoted it.
    Given a store holding a decision type at "https://shop.example/kb/decision"
    Given a title for a new decision that is the number 12 rather than text
    When the client creates a decision with that title, saying which role and why
    Then the title reads back as the text "12"

  @slice-39
  Scenario: The name of a new item comes from its title
    Pins that the store mints an item's name from the item's own title, so a client never chooses names and two clients cannot disagree about them.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step titled "Count what is on the shelf" to the process, saying which role and why
    Then the name the client is given for the new item is made from that title
    And the client never said what the name should be

  @slice-39
  Scenario: An item of a kind that carries no title is named by its place
    Pins the fallback for collections whose items have no title: the store still mints a name, from where the item went in, so every item is addressable.
    Given a store holding a process with two steps and a shared step other processes use
    Given an artifact holding a collection whose items carry no title of their own
    When the client adds an item to that collection, saying which role and why
    Then the name the client is given for the new item is made from its place in the collection

  @slice-39
  Scenario: A second item with a title already used in the collection gets a name of its own
    Pins that names are unique within a collection: a clash is settled by adding a number, and the item already there is never renamed under anything pointing at it.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step whose title is already used by a step of that process, saying which role and why
    Then the name the client is given for the new item is the name already taken with a number added
    And the step already there keeps the name it had

  @slice-39
  Scenario: Taking an item out does not rename the items left
    Pins that a name is minted once and never worked out again, so removing an item cannot quietly move every later item's name out from under a link.
    Given a store holding a process with two steps and a shared step other processes use
    Given an artifact holding a collection whose items carry no title of their own, each named by its place when it was added
    When the client takes the first item out of that collection, saying which role and why
    Then every item left keeps the name it was given when it was added
    And no item is named again from where it now sits

  @slice-14
  Scenario: Putting items in a different order does not rename them
    Pins the same for reordering: order is content, names are identity, and rearranging a collection leaves every link landing where it did.
    Given a store holding a process with two steps and a shared step other processes use
    Given an artifact holding a collection whose items carry no title of their own, each named by its place when it was added
    When the client puts the items of that collection in a different order, saying which role and why
    Then every item keeps the name it was given when it was added
    And anything pointing at one of them still lands on the same item

  Scenario Outline: An added item's title becomes its name, read as text, refused if it leaves nothing
    Pins how an added item's title turns into its name: read as text whatever it looks like, and refused rather than given an empty name when it boils down to nothing.
    Given a store holding a process with two steps and a shared step other processes use
    When the client adds a step titled <title> to the process, saying which role and why
    Then <outcome>

    Examples:
      | title                               | outcome                                                                            |
      | "!!!"                               | the item is rejected because a title must leave something to make a name from      |
      | the number 12 rather than text      | the name the client is given for the new item is made from the text "12"           |
      | the yes-or-no true rather than text | the name the client is given for the new item is made from the text "true"         |

  @slice-86
  Scenario: Items sent back with their names are the same items, and one without a name is new
    Pins what a client sends when it rewrites a whole collection: the names the store gave are what say which item is which, and an item arriving without one is new and is named by the store.
    Given a store holding a decision with a purpose and a rationale, at its first version
    Given the decision carries two options
    When the client replaces the decision, sending both options back with the names they were given and a third option with no name, saying which role and why
    Then the two options are the same items as before, keeping their names
    And the third option is new and is given a name of its own

  @slice-67
  Scenario Outline: Every way an item's name can be wrong on a change is refused
    Pins that item names are the store's to give and the client's only to hand back: anything else is refused rather than stored as the client wrote it.
    Given a store holding a decision with a purpose and a rationale, at its first version
    Given the decision carries two options
    When the client replaces the decision with options <items>, saying which role and why
    Then the change is rejected because <reason>
    And reading the decision gives what it held before, at the version it held before

    Examples:
      | items                                                        | reason                                                                    |
      | one of which carries a name no option of that decision has   | a name on an item names an item already in that collection                |
      | both of which carry the same name                            | the items of a collection each have a name of their own                   |
      | one of which carries a name that is not a plain name         | a name is a plain name of lower-case letters, digits and single hyphens   |

  Scenario: After an artifact has been removed, a new artifact may be created at its IRI
    Pins that an IRI belongs to an artifact for its life and no longer, so a new artifact may take it, starting over at its own first revision.
    Given a store holding a tag type at "https://shop.example/kb/tag"
    Given the client has removed the tag that was held at "https://shop.example/kb/tag/seasonal"
    When the client creates a tag at "https://shop.example/kb/tag/seasonal", saying which role and why
    Then the new tag is held at "https://shop.example/kb/tag/seasonal"
    And the new tag is at its first revision

  Scenario: A part is named by its artifact's IRI, # and its place in it
    Pins how a part inside an artifact is written, so a client can name any part from the artifact's IRI and where the part sits.
    Given a store holding a process at "https://shop.example/kb/process/restock" whose steps include one named draft
    When the client reads "https://shop.example/kb/process/restock#steps/draft"
    Then the client is given the step named draft of that process

  Scenario: A part given a name of the client's choosing on create holds that name
    Pins that a create may name the parts it carries, so the client knows each part's name before the store answers.
    Given a store holding a decision type at "https://shop.example/kb/decision" whose decisions may carry a collection of options
    When the client creates a decision carrying an option it names "keep-weekly", saying which role and why
    Then the option is named "keep-weekly"

  Scenario Outline: A part given no name on create is named by the store from its title or its place
    Pins that a part the client leaves unnamed is named the way an added item is, so every part is addressable from the moment it exists.
    Given a store holding a decision type at "https://shop.example/kb/decision" whose decisions may carry <collection>
    When the client creates a decision carrying <part> with no name, saying which role and why
    Then the part is named <named from>

    Examples:
      | collection                                     | part                                   | named from                                  |
      | a collection of options, each with a title     | an option titled "Keep weekly reviews" | from its title, as an added item would be   |
      | a collection whose items carry no title         | an item                                | from its place, as an added item would be   |

  Scenario: An artifact created giving two parts of one collection the same name is refused
    Pins that a name the client gives a part must tell it apart from the other parts of its collection.
    Given a store holding a decision type at "https://shop.example/kb/decision" whose decisions may carry a collection of options
    When the client creates a decision carrying two options it names both "keep-weekly", saying which role and why
    Then the artifact is rejected because a part's name is unique in its collection
    And the refusal names "keep-weekly"
    And nothing is written

  Scenario: An artifact created giving a part a name that is not a plain name is refused
    Pins that a name the client gives a part keeps to the grammar of names the store gives, so every part can be written into an IRI.
    Given a store holding a decision type at "https://shop.example/kb/decision" whose decisions may carry a collection of options
    When the client creates a decision carrying an option it names "Keep Weekly!", saying which role and why
    Then the artifact is rejected because a part's name is a plain name
    And the refusal names the place of that option
    And nothing is written
