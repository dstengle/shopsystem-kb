Feature: Define a type
So that a client decides for itself what its artifacts are made of, the client can define a type.

  Background:
    Given a store

  @slice-1
  Scenario: The client defines a type
    Pins that types are data: a type is an ordinary artifact written through the same door as everything else, so a client can add one without the store knowing anything about its domain.
    When the client defines a type whose artifacts carry a title, a body, a link to another artifact of the same type, two required sections in order, and a collection of parts
    Then the type is an artifact the client can read back like any other
    And artifacts of that type can be created

  @slice-2
  Scenario: Two types share a shape
    Pins that one type can name a shape another type defines, so a client describes a shared shape once instead of repeating it wherever it is used.
    Given a type that defines the shape of a binding
    When the client defines a second type that refers to that shape
    Then artifacts of the second type are checked against the shape the first type defines

  @slice-3
  Scenario: A type built on a shared base carries the base's fields and sections
    Pins how types share common ground without inheritance: a type built on a base is checked against both, with the base's required sections coming first.
    Given a base type that gives every artifact an owner and a status, and requires a purpose section
    When the client defines a decision type built on that base, adding a rationale section of its own
    Then a decision missing its owner is rejected because it does not fit its type
    And a decision reads back with its purpose before its rationale

  @slice-27
  Scenario: Something that is not a well-formed type is refused
    Pins that types are checked too, against the one type the store ships, so a broken type is caught when it is written rather than by every artifact that uses it.
    When the client defines a type that does not match the type that describes types
    Then the type is rejected because it does not match the type that describes types
