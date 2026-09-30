# formulated from spec/capabilities/review-the-files-on-disk.md
Feature: Review the files on disk
  Narrator: the operator

  @slice-1.1
  Scenario: The operator reads an artifact's file on disk
    Pins that the files are meant to be read and reviewed by people: prose in blocks, lists under their names, no rewrapping, and nothing in them that instructs a reader how to build a value.
    Given a store holding a decision whose purpose is one short line and which carries a list of options
    When the operator opens the decision's file
    Then every piece of prose stands as a block of its own, however short it is
    And each list is written beneath the name it belongs to, indented under it
    And no line of prose has been broken to fit a width
    And nothing in the file tells a reader how to build a value

  @slice-1.9
  Scenario: The same content always lands on disk as the same bytes
    Pins that writing is deterministic, which is what makes a difference between two versions mean a real change rather than a reshuffle.
    Given two stores each given the same decision by the same client
    When the operator compares the two decision files
    Then the two files are the same, byte for byte
