Feature: Read an artifact
So that a client can show what the store holds at whatever depth it needs, the client can read an artifact.

  Background:
    Given a store holding a decision that supersedes an older decision, has a purpose and a rationale, carries two options, and is pointed at by two work items

  @slice-1
  Scenario: The client reads a summary
    Pins the walking skeleton's read, and the belief it rests on: a summary carries enough of the surroundings that a client can move through the store without reading anything whole.
    When the client reads the decision at a glance
    Then the client is given its name, its kind, its title and the few fields the type shows at a glance
    And a stub of each thing it points at and of each of its parts
    And how many things point at it, counted by their kind and by the link they use

  @slice-21
  Scenario: The client reads one section by its title
    Pins the read the store expects to see most: one section by name, and nothing else carried along with it.
    When the client reads the rationale of the decision
    Then the client is given that section and nothing else

  @slice-21
  Scenario: The client reads the whole artifact
    Pins the full read, and that what comes back is in the order the type declares rather than the order it happened to be written.
    When the client reads the whole decision
    Then the client is given every field, every section and every part, in the order the type declares

  @slice-21
  Scenario: Without being asked to follow them, links come back as names
    Pins the default: a read does not drag in the neighbourhood unasked, so the cost of a read is the artifact and no more.
    When the client reads the whole decision without asking for its links to be followed
    Then the older decision is given as the name it is known by, and nothing more

  @slice-21
  Scenario: The client reads the whole artifact with what it points at filled in
    Pins the one-step fill-in, and that it stops there: what the neighbour points at is still just names.
    When the client reads the whole decision following its links one step
    Then the older decision is given in place of the link, as the store holds it now
    And what the older decision itself points at is given as names

  @slice-21
  Scenario: The client reads an artifact following its links two steps
    Pins that the depth asked for is honoured all the way down, so a client can pull back exactly as much of the graph as it means to show.
    Given the older decision is tagged "pricing"
    When the client reads the whole decision following its links two steps
    Then the older decision is given in place of the link
    And the tag is given in place of the link inside the older decision

  @slice-12
  Scenario: A loop in the links stops instead of going round
    Pins that a circle in the graph is safe to read: anything already filled in on the way comes back as a name, so a read ends.
    Given two decisions that point at each other
    When the client reads the whole of one of them following its links three steps
    Then the other decision is given in place of the link
    And where that one points back, the decision being read is given as a name rather than filled in again

  @slice-21
  Scenario: The branches inside a process are not followed
    Pins the line between a link between artifacts and a step naming a step beside it, so following links does not unroll a process's own flow.
    Given a store holding a process whose steps branch to other steps of the same process
    When the client reads the whole process following its links one step
    Then the branches are given as written, naming the steps of that process

  @slice-1.7
  Scenario: Reading something the store does not hold is refused
    Pins that a name the store does not know is an answer that names it back, so a client can tell "not here" from "went wrong".
    When the client reads an artifact by a name the store holds nothing under
    Then the read is rejected because the store holds nothing by that name, and the name asked for is given back

  @slice-1.7
  Scenario: A name that is not a plain name is refused
    Pins that a name is checked for shape before any file is found from it, so a name built to walk out of the store reads nothing at all.
    When the client reads an artifact by the name "decision/../elsewhere"
    Then the read is rejected because a name is a kind and a plain name of lower-case letters, digits and single hyphens
    And no content comes back, from inside the store or outside it

  @slice-1.7
  Scenario: A name that begins at the root of the disk is refused
    Pins the same for a name that is simply a path from the top of the disk, which is the other obvious way to ask for a file that is none of the store's business.
    When the client reads an artifact by a name that begins at the root of the disk
    Then the read is rejected because a name is a kind and a plain name, never a path
    And no content comes back, from inside the store or outside it

  @slice-1.7
  Scenario: A place inside an artifact that is not a plain place is refused
    Pins that the place inside an artifact is checked just as strictly as the name, so nothing escapes through the second half of a locator.
    When the client reads the place "sections/../.." inside the decision
    Then the read is rejected because a place inside an artifact is named by parts of the same plain alphabet, or a collection and an item in it
    And no content comes back, from inside the store or outside it

  @slice-1.3
  Scenario: The client works in a folder inside the store
    Pins that a client finds its store by looking upward from where it is working, the way git finds a repository.
    Given the client is working in a folder deep inside the directory the store sits in
    When the client reads the decision
    Then the client is given the decision, from the store found above where it is working

  @slice-1.8
  Scenario: The client names the store instead of working inside it
    Pins the other way of saying which store is meant, for a client that runs from outside one.
    Given the client is working outside any store, with KB_ROOT naming this one
    When the client reads the decision
    Then the client is given the decision, from the store KB_ROOT names

  @slice-1.8
  Scenario: A call with no store to be found is refused
    Pins that finding no store is a refusal the client can handle, not an exception thrown out of a call.
    Given the client is working outside any store and nothing names one
    When the client reads the decision
    Then the read is rejected because no store was found, neither above where it is working nor named outright

  @slice-1.8
  Scenario: Naming a store that is not there is refused
    Pins that naming a store that is not there is its own refusal, rather than a silent fall back to looking upward.
    Given the client is working outside any store, with KB_ROOT naming a directory that holds no store
    When the client reads the decision
    Then the read is rejected because KB_ROOT names a directory that holds no store
    And no content comes back

  @slice-1.8
  Scenario: Working in one store while naming another is refused
    Pins that two candidate stores is a refusal and never a preference, so a read never quietly comes from somewhere the client did not expect.
    Given the client is working inside a store, with KB_ROOT naming a different store
    When the client reads the decision
    Then the read is rejected because KB_ROOT names a store other than the one it is working in, and neither of the two is guessed at
    And no content comes back, from either store

  @slice-1.15
  Scenario: A client readied before there was a store finds the store started since
    Pins that a client binds to no store when it is made and works out where it is on every call, so long-lived clients and fresh stores do not need ordering.
    Given the client was readied to call a store while working where there was none and nothing named one
    And a store holding the decision has since been started where the client is working
    When the client reads the decision
    Then the client is given the decision
    And the client was never readied again after the store appeared

  @slice-1.19
  Scenario: Reading an artifact whose stored file cannot be read is refused
    Pins that damage done behind the store's back surfaces as an ordinary named fault, so one broken file cannot take a client down.
    Given someone edited the decision's file by hand and left it in a shape the store cannot read
    When the client reads the decision
    Then the read is rejected because that file cannot be read, and the file is named
    And the client is given that fault as it is given any other, the call never breaking off
