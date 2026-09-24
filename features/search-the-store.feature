Feature: Search the store
So that a client can find content without knowing where it sits, the client can search the store.

  Background:
    Given a store where two decisions and a process mention restocking in their prose

  @slice-10
  Scenario: The client searches the prose
    Pins what a result has to carry to be useful: which section matched and a glimpse of it, with the strongest match first.
    When the client searches the prose for restocking
    Then each result comes with the title of the section it matched and a snippet of it
    And the one whose section mentions restocking most often comes first

  @slice-33
  Scenario: The client searches within one kind
    Pins that a search can be held to one kind, so a client looking for a decision is not handed everything else that says the same word.
    When the client searches the prose for restocking among decisions only
    Then the client is given the two decisions and not the process

  @slice-33
  Scenario: The client searches the fields as well as the prose
    Pins that a search can reach beyond prose into the typed fields, catching matches that live in a title rather than a body.
    When the client searches the fields and the prose for restocking
    Then the client is also given a decision whose title mentions restocking
