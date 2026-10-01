"""kb's command line in a program of its own whose store waits for the write lock as long as it is told, for a test
that holds the lock (held.operator); everything else as the console command runs it.

    python operator_program.py <seconds> <kb's arguments>
"""
import sys

from kb import cli, sqlite_store

if __name__ == "__main__":
    sqlite_store.BUSY = float(sys.argv[1])
    sys.exit(cli.main(sys.argv[2:]))
