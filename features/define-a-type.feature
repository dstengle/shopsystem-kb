# formulated from spec/capabilities/define-a-type.md
Feature: Define a type
  Narrator: the client

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

  @slice-68
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

  Scenario: A link field declared where kb does not read one is refused
    Pins that a link field only counts where kb reads it, so a link that would silently never be followed is refused when the type is written.
    When the client defines a type that declares a link field inside a field's own nested schema
    Then the type is rejected because kb does not read a link field there
    And the refusal names the place
    And nothing is written anywhere in the store

  Scenario: Collections declared where kb does not read them are refused
    Pins that a collection only counts at the top of a schema or of a collection's items, so one that would never hold parts is refused when the type is written.
    When the client defines a type that declares a collection inside a field's own nested schema
    Then the type is rejected because kb does not read them there
    And the refusal names the place
    And nothing is written anywhere in the store

  Scenario: Required sections declared where kb does not read them are refused
    Pins that required sections only count at the top of a schema, so sections that would never be required are refused when the type is written.
    When the client defines a type that declares required sections inside a collection's items
    Then the type is rejected because kb does not read them there
    And the refusal names the place
    And nothing is written anywhere in the store

  Scenario: Fields shown at a glance declared where kb does not read them are refused
    Pins that the fields shown at a glance only count at the top of a schema or of a collection's items, so a choice that would never show is refused when the type is written.
    When the client defines a type that declares the fields shown at a glance inside a field's own nested schema
    Then the type is rejected because kb does not read them there
    And the refusal names the place
    And nothing is written anywhere in the store

  Scenario Outline: A link field that leaves out part of what it must say is refused
    Pins that a link field is only accepted when it is complete, so a link whose behaviour kb would have to guess is refused when the type is written.
    When the client defines a type with a link field that does not say <what is left out>
    Then the type is rejected because a link field says which kinds it may point at, whether it points at one artifact or several, whether it may point into a part and what a removal does
    And the refusal names the place
    And nothing is written anywhere in the store

    Examples:
      | what is left out                             |
      | whether it points at one artifact or several |
      | whether it may point into a part             |
      | what a removal does                          |

  Scenario: A link field whose removal rule is not refuse is refused
    Pins that refuse is the only removal rule kb knows, so a link promising another behaviour is refused when the type is written.
    When the client defines a type with a link field whose removal rule is cascade
    Then the type is rejected because refuse is the one removal rule kb knows
    And the refusal names the place
    And nothing is written anywhere in the store

  Scenario: A link field that points at neither one artifact nor several is refused
    Pins that a link points at one artifact or several and nothing else, so a link with any other reach is refused when the type is written.
    When the client defines a type with a link field that says it points at two artifacts
    Then the type is rejected because a link field points at one artifact or several
    And the refusal names the place
    And nothing is written anywhere in the store

  Scenario Outline: A type may use any keyword that is not kb's own, anywhere in its schema
    Pins that kb restricts only its own keywords, so a client has the whole of JSON Schema 2020-12 beside them.
    When the client defines a type that uses <keyword> inside a field's own nested schema
    Then the type is accepted
    And artifacts of that type can be created

    Examples:
      | keyword |
      | enum    |
      | pattern |
      | format  |

  Scenario: A held type that carries a keyword where kb does not read it stays as it is
    Pins that tightening where kb's keywords may stand does not reach back into a store, so a type written before it is not altered.
    Given a type the store holds that carries one of kb's keywords where kb does not read it
    When the client reads that type
    Then the type reads back as it was

  Scenario: Changing a held type that still carries a keyword where kb does not read it is refused
    Pins that a held type is checked against the placement rule when it is changed, so it cannot be changed while the keyword stays where kb does not read it.
    Given a type the store holds that carries one of kb's keywords where kb does not read it
    When the client changes that type, moving its version on and leaving the keyword where it is
    Then the change is rejected because kb does not read it there
    And the refusal names the place

  @slice-71
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

  @slice-84
  Scenario: A type changed without moving its version on is refused
    Pins that a type's version is the only thing that tells an artifact it has fallen behind, so a type cannot change under its artifacts while still claiming the version they were checked against.
    Given a type the store holds at its second version
    When the client changes what that type requires, leaving its version at two
    Then the change is rejected because a type's version goes up whenever the type changes
    And the type reads back as it was

  @slice-106
  Scenario: Removing a type while the store holds artifacts of its kind is refused
    Pins that a type cannot be taken away from under the artifacts it checks, and that the client is told exactly which artifacts stand in the way.
    Given a type the store holds, and two artifacts of its kind
    When the client removes that type
    Then the removal is rejected because something still points at it, naming each of those two artifacts
