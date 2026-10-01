"""The installed `kb` console command runs kb's command line: the steps run that command line in their own process
(conftest._kb), and this one test runs the command itself, as the operator does, in a directory of its own."""
import os
import subprocess
import sys
from pathlib import Path

KB = Path(sys.executable).with_name("kb")


def test_the_kb_command_runs_the_command_line(tmp_path):
    env = {key: value for key, value in os.environ.items() if key not in ("KB_ROOT", "KB_ACTOR")}
    started = subprocess.run([str(KB), "init", str(tmp_path)], cwd=tmp_path, env={**env, "KB_ACTOR": "operator"},
                             capture_output=True, text=True)
    assert (started.returncode, started.stderr) == (0, "")
    checked = subprocess.run([str(KB), "validate"], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert (checked.returncode, checked.stdout, checked.stderr) == (0, "", "")
