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

  @slice-156
  Scenario: The client defines a type, giving it an https IRI of kb's grammar
    Pins that a type lives at the IRI its client chooses, its version beside it under a number, and its artifacts beneath it.
    When the client defines a type, giving it the IRI "https://example.com/shop/decision"
    Then the type is held at "https://example.com/shop/decision"
    And its version is held at "https://example.com/shop/decision", "@" and the version's number
    And an artifact created of that type has an IRI under "https://example.com/shop/decision"

  @slice-156
  Scenario: A type's IRI need not sit under the IRI of the type that describes types
    Pins that a type is exempt from the rule that an artifact sits under its type, so a client may put its types anywhere.
    When the client defines a type, giving it the IRI "https://example.com/shop/decision", which does not sit under "https://missingmass.io/kb/type"
    Then the type is accepted
    And the type is held at "https://example.com/shop/decision"

  @slice-161
  Scenario: The client changes a type
    Pins that a change to a type never alters what was made before it, but adds a version of its own beside the earlier ones.
    Given a type the store holds at "https://example.com/shop/decision", changed once since it was defined
    When the client changes what that type requires
    Then the change makes a new version at "https://example.com/shop/decision", "@" and the new version's number
    And the version the type was defined with reads back as it was made
    And the version its first change made reads back as it was made

  @slice-161
  Scenario: The client changes a type and the store numbers the new version
    Pins that the store, not the client, numbers a type's versions, one after another.
    Given a type the store holds at its second version
    When the client changes that type
    Then the new version is the type's third

  @slice-161
  Scenario: While an artifact conforms to a version of a type, the store holds that version
    Pins that a version an artifact still conforms to is never lost when its type moves on.
    Given a type the store holds at its first version, and an artifact conforming to that version
    When the client changes that type
    Then the store still holds the type's first version
    And the artifact still conforms to the type's first version

  @slice-161
  Scenario: When no artifact conforms to a version of a type any longer, the store still holds that version
    Pins that the store does not clear away a version once nothing uses it.
    Given a type the store holds at its second version, and the only artifact conforming to its first version
    When the client removes that artifact
    Then the store still holds the type's first version

  @slice-165
  Scenario: A link field naming a kind by its type's IRI may point at an artifact of any version of that type
    Pins that a link names a kind and not a version, so moving a type on does not cut off the artifacts already of its kind.
    Given a decision type the store holds at its second version, a decision conforming to its first version and a decision conforming to its second
    And a type whose link field names the kinds it may point at by the decision type's IRI
    When the client creates an artifact of that type pointing through that field at both decisions
    Then the artifact is created
    And it points at both decisions

  @slice-156
  Scenario: The type that describes types is held at its own IRI
    Pins where the one type the store ships lives, so a client can name it and read it like any other type.
    When the client reads "https://missingmass.io/kb/type"
    Then it reads back the type that describes types
    And its version is held at "https://missingmass.io/kb/type", "@" and the version's number

  @slice-165
  Scenario: A type refers to a shape another type defines, naming the version it reads
    Pins that a shared shape is read from the version a type names, so moving the other type on does not change what the referring type checks.
    Given a type that defines the shape of a binding, whose first version requires a binding to give a name, and whose second version requires a name and a port
    When the client defines a second type that refers to the binding's shape, naming the first version of that type by its IRI
    Then an artifact of the second type whose binding gives a name and no port is accepted
    And an artifact of the second type whose binding gives no name is rejected because it does not fit its type

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

  @slice-165
  Scenario Outline: A type that could never check an artifact is refused when it is written
    Pins that a type is checked the moment it is written, so a type that could never check an artifact is caught once here rather than by every create that tries to use it, and the client is told which fault it has.
    Given a binding type the store holds at its second version
    When the client defines a type that <fault>
    Then the type is rejected because it could never check an artifact
    And the refusal names that the type <fault>
    And nothing is written anywhere in the store

    Examples:
      | fault                                                                    |
      | refers to a shape from a version of a type the store does not hold at all |
      | refers to a shape from the third version of the binding type             |
      | names itself as the type it is built on                                  |
      | declares a link field without saying which kinds it may point at         |

  @slice-125
  Scenario: A link field declared where kb does not read one is refused
    Pins that a link field only counts where kb reads it, so a link that would silently never be followed is refused when the type is written.
    When the client defines a type that declares a link field inside a field's own nested schema
    Then the type is rejected because kb does not read a link field there
    And the refusal names the place
    And nothing is written anywhere in the store

  @slice-125
  Scenario: Collections declared where kb does not read them are refused
    Pins that a collection only counts at the top of a schema or of a collection's items, so one that would never hold parts is refused when the type is written.
    When the client defines a type that declares a collection inside a field's own nested schema
    Then the type is rejected because kb does not read them there
    And the refusal names the place
    And nothing is written anywhere in the store

  @slice-125
  Scenario: Required sections declared where kb does not read them are refused
    Pins that required sections only count at the top of a schema, so sections that would never be required are refused when the type is written.
    When the client defines a type that declares required sections inside a collection's items
    Then the type is rejected because kb does not read them there
    And the refusal names the place
    And nothing is written anywhere in the store

  @slice-125
  Scenario: Fields shown at a glance declared where kb does not read them are refused
    Pins that the fields shown at a glance only count at the top of a schema, so a choice that would never show is refused when the type is written.
    When the client defines a type that declares the fields shown at a glance inside a field's own nested schema
    Then the type is rejected because kb does not read them there
    And the refusal names the place
    And nothing is written anywhere in the store

  @slice-125
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

  @slice-125
  Scenario: A link field whose removal rule is not refuse is refused
    Pins that refuse is the only removal rule kb knows, so a link promising another behaviour is refused when the type is written.
    When the client defines a type with a link field whose removal rule is cascade
    Then the type is rejected because refuse is the one removal rule kb knows
    And the refusal names the place
    And nothing is written anywhere in the store

  @slice-125
  Scenario: A link field that points at neither one artifact nor several is refused
    Pins that a link points at one artifact or several and nothing else, so a link with any other reach is refused when the type is written.
    When the client defines a type with a link field that says it points at two artifacts
    Then the type is rejected because a link field points at one artifact or several
    And the refusal names the place
    And nothing is written anywhere in the store

  @slice-126
  Scenario: A type refused with several faults has them given in the order its places stand when it reads back
    Pins that a refused type's faults follow the order the type reads back in, which is the order the client wrote it in, and that faults at one place are told apart by a fixed order of their rules.
    When the client defines a type where one field breaks two of kb's rules for a link field, a field's nested schema declares required sections, and a collection's items declare required sections
    Then the type is rejected with every fault, each naming the place
    And the faults come in the order the places stand in the type as it reads back, which is the order the client wrote it in
    And the two faults at the link field come in the alphabetical order of the names of the rules they break
    And nothing is written anywhere in the store

  @slice-125
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

  @slice-164
  Scenario: A type is changed so that artifacts the store holds would no longer fit it
    Pins that a type may move on past its artifacts: they stay with the version they named and are reported as behind, never as broken.
    Given a decision type the store holds at its first version, which does not require an owner, and a decision with no owner
    When the client changes the decision type to require an owner
    Then the change is accepted as the type's second version
    And the decision still conforms to the type's first version
    And checking the store lists the decision as behind its type, not as a violation

  Scenario: A type is changed and the links of an artifact conforming to its earlier version stay as that version declares
    Pins that changing a type rewrites nothing about the artifacts left at its earlier version: a link their version declares still guards what it points at, and a field only the new version makes a link is not one for them.
    Given a note type the store holds at its first version, whose notes link to a tag and hold a reference as plain text
    And a tag, and a note conforming to that version that links to the tag and holds a reference
    When the client changes the note type so that notes no longer link to a tag and their reference is a link
    Then removing the tag is rejected because something still points at it, naming the note
    And the note's reference is not a link

  @slice-106
  Scenario: Removing a type while the store holds artifacts of its kind is refused
    Pins that a type cannot be taken away from under the artifacts it checks, and that the client is told exactly which artifacts stand in the way.
    Given a type the store holds, and two artifacts of its kind
    When the client removes that type
    Then the removal is rejected because something still points at it, naming each of those two artifacts
