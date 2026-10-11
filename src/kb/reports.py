"""What the operator's commands print to stdout of what they found: the check's three lists, one to a line, and the
import's report. Printing only; what a refusal prints, and the exit codes, are the commands'."""
from kb import names


def checked(result) -> None:
    """The check's lists: every violation, then every artifact behind its type, then every link into a placeholder,
    with the part it names, one to a line."""
    for fault in result.violations:
        print("\t".join(("violation", fault.artifact, fault.place, fault.rule, fault.message)))
    for stale in result.stale:
        print(f"stale\t{stale.artifact}\tchecked against version {stale.schema_version} of its type, "
              f"which is at {stale.current}")
    for placeholder in result.placeholders:
        for link in placeholder.links:
            print("\t".join(("placeholder", names.pointing(placeholder.id, link.part), link.artifact, link.place)))


def imported(report) -> None:
    """The import's report: every error, then every file that would be skipped with the chain of files leading to a
    broken one, one to a line."""
    for fault in report.errors:
        print("\t".join(("error", fault.artifact, fault.rule, fault.message)))
    for skipped in report.skipped:
        print("\t".join(("skipped", skipped.file, " -> ".join(skipped.chain))))
