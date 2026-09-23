Feature: Define a type
So that a client decides for itself what its artifacts are made of, the client can define a type.

  Background:
    Given a store

  @slice-1
  Scenario: The client defines a type
    When the client defines a type whose artifacts carry a title, a body, a link to another artifact of the same type, two required sections in order, and a collection of parts
    Then the type is an artifact the client can read back like any other
    And artifacts of that type can be created

  @slice-2
  Scenario: Two types share a shape
    Given a type that defines the shape of a binding
    When the client defines a second type that refers to that shape
    Then artifacts of the second type are checked against the shape the first type defines

  @slice-3
  Scenario: A type built on a shared base carries the base's fields and sections
    Given a base type that gives every artifact an owner and a status, and requires a purpose section
    When the client defines a decision type built on that base, adding a rationale section of its own
    Then a decision missing its owner is rejected because it does not fit its type
    And a decision reads back with its purpose before its rationale

  @slice-34
  Scenario: Something that is not a well-formed type is refused
    When the client defines a type that does not match the type that describes types
    Then the type is rejected because it does not match the type that describes types
