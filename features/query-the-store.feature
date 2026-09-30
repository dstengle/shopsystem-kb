# formulated from spec/capabilities/query-the-store.md
Feature: Query the store
  Narrator: the client

  @slice-29
  Scenario: The client lists every artifact of a kind
    Pins the way into the store when a client knows no names at all: ask by kind and get a stub of each one.
    Given a store holding three decisions, one of them superseded
    When the client lists the decisions
    Then the client is given a stub of each of the three

  @slice-29
  Scenario: The client lists the artifacts matching a field
    Pins that a listing can be narrowed by a field, so the common "show me only these" question is answered by the store rather than by the client sifting.
    Given a store holding three decisions, one of them superseded
    When the client lists the decisions that are superseded
    Then the client is given only the superseded one

  @slice-29
  Scenario: The client lists names only
    Pins that a client can ask for just the names, for when it means to work through them one by one and does not want everything up front.
    Given a store holding three decisions, one of them superseded
    When the client lists the decisions asking for names only
    Then the client is given three names and nothing else

  @slice-31
  Scenario: The client follows the links out of an artifact
    Pins the simplest traversal: what an artifact points at comes back as stubs, enough to show without reading each target whole.
    Given a store where a decision supersedes an older decision
    And two work items point at that decision
    And the older decision is tagged "pricing"
    When the client follows the links out of the decision
    Then the client is given a stub of the older decision

  @slice-31
  Scenario: The client follows the links into an artifact
    Pins that the store knows who points at a thing as well as what it points at, which is the question no single artifact can answer by itself.
    Given a store where a decision supersedes an older decision
    And two work items point at that decision
    And the older decision is tagged "pricing"
    When the client follows the links into the decision
    Then the client is given a stub of each work item

  @slice-89
  Scenario: The client narrows the links to one link and one kind
    Pins that a traversal can be narrowed to one link and one kind, so a client asks its real question instead of filtering everything afterwards.
    Given a store where a decision supersedes an older decision
    And two work items point at that decision
    And the older decision is tagged "pricing"
    Given a note that is not a work item also points at the decision, through the same link the work items use
    And one of the two work items points at the decision a second time, through a different link of its own
    When the client follows the links into the decision, only through the link a work item uses, and only from work items
    Then the client is given both work items and nothing else

  @slice-11
  Scenario: The client follows the links two steps out
    Pins that a traversal can go more than one step and reports the route to each thing found, so a client can explain why something turned up.
    Given a store where a decision supersedes an older decision
    And two work items point at that decision
    And the older decision is tagged "pricing"
    When the client follows the links out of the decision two steps
    Then the client is given the older decision and the tag
    And each of them comes with the route taken to it

  @slice-89.2
  Scenario: The client follows the links out of one place inside an artifact
    Pins that a traversal can start at a place inside an artifact rather than the whole of it, so a client can ask what one step points at and get only that.
    Given a store where a decision supersedes an older decision
    And two work items point at that decision
    And the older decision is tagged "pricing"
    Given a process one of whose steps points at a tag of its own, while another of its steps points at the decision
    When the client follows the links out of that step of the process
    Then the client is given a stub of that tag and nothing else the process points at

  @slice-72
  Scenario: A link into a part counts as a link into the artifact holding it
    Pins that pointing at a part is pointing at the artifact it sits in, so the count at a glance, the links coming in, and what blocks a removal all agree with one another.
    Given a store where a decision supersedes an older decision
    And two work items point at that decision
    And the older decision is tagged "pricing"
    Given a store holding a process, and a work item that points at one step of that process rather than at the whole process
    When the client follows the links into the process
    Then the client is given a stub of that work item
    And reading the process at a glance counts that work item among the things pointing at it
    And removing the process is refused while that work item points into it

  @slice-10
  Scenario: The client searches the prose
    Pins what a result has to carry to be useful: which section matched and a glimpse of it, with the strongest match first.
    Given a store where two decisions and a process mention restocking in their prose
    When the client searches the prose for restocking
    Then each result comes with the title of the section it matched and a snippet of it
    And the one whose section mentions restocking most often comes first

  @slice-33
  Scenario: The client searches within one kind
    Pins that a search can be held to one kind, so a client looking for a decision is not handed everything else that says the same word.
    Given a store where two decisions and a process mention restocking in their prose
    When the client searches the prose for restocking among decisions only
    Then the client is given the two decisions and not the process

  @slice-33
  Scenario: The client searches the fields as well as the prose
    Pins that a search can reach beyond prose into the typed fields, catching matches that live in a title rather than a body.
    Given a store where two decisions and a process mention restocking in their prose
    When the client searches the fields and the prose for restocking
    Then the client is also given a decision whose title mentions restocking
