# formulated from spec/capabilities/name-artifacts-and-items.md
Feature: Name artifacts and items
  Narrator: the client

  @slice-25
  Scenario: The name of a new artifact is made from its title, not asked for
    Pins that names are minted by the store from the title, so a client cannot choose one and never has to invent one.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision titled "Price reviews happen weekly", saying which role and why
    Then the name the client is given is made from that title
    And the client never said what the name should be

  @slice-8.1
  Scenario: A second artifact with a title already used gets a name of its own
    Pins how a clash is settled: the newcomer takes a numbered name and the artifact already there keeps the name everything else points at.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    Given a decision the store already holds, titled "Price reviews happen weekly"
    When the client creates another decision with that same title, saying which role and why
    Then the client is given a name of its own for the new decision, the name already taken with a number added
    And the decision created first keeps the name it had

  @slice-25
  Scenario: Two parts with the same title are given names of their own
    Pins that parts are named by the same rules as artifacts, including the clash rule, so every part inside a new artifact is addressable from the moment it exists.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision carrying two options with the same title, saying which role and why
    Then each option is given a name of its own, the second the name of the first with a number added
    And the client never said what either name should be

  @slice-1.6
  Scenario: A title with capitals and punctuation gives a plain name
    Pins exactly how a title becomes a name, so the same title always gives the same name and every name is safe to put in a path or a link.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision titled "Price reviews: weekly, from now on!", saying which role and why
    Then the name the client is given is that title in lower case, with each run of anything that is not a letter or a digit turned into a single hyphen, and no hyphen at either end

  @slice-1.6
  Scenario: A title that leaves nothing to make a name from is refused
    Pins the edge of that rule: rather than invent a name when the title boils down to nothing, the store refuses and says why.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision titled "!!!", saying which role and why
    Then the artifact is rejected because a title must leave something to make a name from

  @slice-1.5
  Scenario: A title that reads as a date is still a title
    Pins that a title is always text: nothing quietly reads it as a date on the way in and hands back something the client never wrote.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision titled "2026-09-24", saying which role and why
    Then the title reads back as the text that was written, not as a date
    And the name the client is given is made from that text

  @slice-1.6
  Scenario: A title that reads as yes is still a title
    Pins the same for the words older readers turn into yes and no, which is the classic way a title comes back as something else entirely.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    When the client creates a decision titled "yes", saying which role and why
    Then the title reads back as the text that was written, not as a yes or a no
    And the name the client is given is made from that text

  @slice-1.18
  Scenario: A title given as a yes-or-no is still a title
    Pins that a title is turned into text whatever arrives, so a client that sends an unquoted word still gets a title and a name it can use.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    Given a title for a new decision that is the yes-or-no true rather than text
    When the client creates a decision with that title, saying which role and why
    Then the title reads back as the text "true"
    And the name the client is given is made from that text

  @slice-1.25
  Scenario: A title given as a number is still a title
    Pins the same for a number, which is how a title like a year or a version arrives when nobody quoted it.
    Given a store holding a decision type whose artifacts require a purpose then a rationale, may link to the decision they supersede, and may carry a collection of options
    Given a title for a new decision that is the number 12 rather than text
    When the client creates a decision with that title, saying which role and why
    Then the title reads back as the text "12"
    And the name the client is given is made from that text

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

  @slice-80
  Scenario Outline: An item's title becomes its name by the same rules as an artifact's title
    Pins that one rule turns a title into a name everywhere: an item's title is read as text whatever it looks like, and a title that leaves nothing to make a name from is refused rather than given an empty name.
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

  @slice-87
  Scenario: A name is free again once what held it has been removed
    Pins that a name belongs to an artifact for its life and no longer, so the next artifact whose title gives that name simply takes it, at its own first version.
    Given a store holding a tag nothing points at
    And a tag a decision points at
    Given the client has removed the tag nothing points at
    When the client creates a tag with the title the removed one had, saying which role and why
    Then the client is given the name the removed tag had, with no number added
    And the new tag is at its first version
