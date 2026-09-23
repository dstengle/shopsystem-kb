Feature: Search the store
So that a client can find content without knowing where it sits, the client can search the store.

  Background:
    Given a store where two decisions and a process mention restocking in their prose

  @assumes-typed-refs-cover-the-questions
  Scenario: The client searches the prose
    When the client searches the prose for restocking
    Then each result comes with the title of the section it matched and a snippet of it
    And the one whose section mentions restocking most often comes first

  @assumes-typed-refs-cover-the-questions
  Scenario: The client searches within one kind
    When the client searches the prose for restocking among decisions only
    Then the client is given the two decisions and not the process

  @assumes-typed-refs-cover-the-questions
  Scenario: The client searches the fields as well as the prose
    When the client searches the fields and the prose for restocking
    Then the client is also given a decision whose title mentions restocking
