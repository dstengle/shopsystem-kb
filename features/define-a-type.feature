Feature: Define a type
So that a client decides for itself what its artifacts are made of, the client can define a type.

  Background:
    Given a store

  @assumes-types-are-data
  Scenario: The client defines a type
    When the client defines a type whose artifacts carry a title, a body, a link to another artifact of the same type, two required sections in order, and a collection of parts
    Then the type is an artifact the client can read back like any other
    And artifacts of that type can be created

  @assumes-shared-shapes-come-from-cross-type-references
  Scenario: Two types share a shape
    Given a type that defines the shape of a binding
    When the client defines a second type that refers to that shape
    Then artifacts of the second type are checked against the shape the first type defines

  @assumes-types-are-data
  Scenario: Something that is not a well-formed type is refused
    When the client defines a type that does not match the type that describes types
    Then the type is rejected because it does not match the type that describes types
