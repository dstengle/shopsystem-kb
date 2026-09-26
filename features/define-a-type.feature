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

  Scenario Outline: A type the store could never check anything against is refused when it is written
    Pins that a type is checked the moment it is written, so a type that could never check an artifact is caught once here rather than by every create that tries to use it.
    When the client defines a type that <fault>
    Then the type is rejected because <reason>
    And nothing is written anywhere in the store

    Examples:
      | fault                                                          | reason                                                       |
      | refers to a shape from a type the store does not hold          | a shape a type refers to must belong to a type the store holds |
      | names itself as the type it is built on                        | a type cannot be built on itself                             |
      | declares a link field without saying which kinds it may point at | a link field says which kinds it may point at              |

  Scenario Outline: A type built on a base carries everything the base declares, of every kind
    Pins that a base is carried in full and not only its fields and sections, so a client can put anything a type is made of into a base and have it hold for every type built on it.
    Given a base type declaring <what the base declares>
    When the client defines a decision type built on that base, adding a rationale section of its own
    Then <what a client observes>

    Examples:
      | what the base declares                          | what a client observes                                                                        |
      | a collection of notes every artifact may carry  | a decision of that type can be given notes, and each note is named by the store               |
      | which fields are shown at a glance              | reading a decision of that type at a glance shows the base's fields as well as the type's own |
      | a link field every artifact may carry           | a decision of that type pointing through that field at a kind the base does not allow is rejected |

  Scenario: A type changed without moving its version on is refused
    Pins that a type's version is the only thing that tells an artifact it has fallen behind, so a type cannot change under its artifacts while still claiming the version they were checked against.
    Given a type the store holds at its second version
    When the client changes what that type requires, leaving its version at two
    Then the change is rejected because a type's version goes up whenever the type changes
    And the type reads back as it was
