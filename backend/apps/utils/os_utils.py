import os
import subprocess
from subprocess import CompletedProcess
from typing import Dict, List


def run_cmd(cmd: List[str], cwd: str = None, raise_on_non_zero_code: bool = False, additional_env: Dict = {}) -> CompletedProcess:
    """

    Args:
        cmd (List[str]): List of the command and its arguments.
        cwd (str, optional): Working directory in which the command should run.

    Returns:
        CompletedProcess
    """
    env = {**os.environ, **additional_env}
    completed_process = subprocess.run(args=cmd, cwd=cwd, capture_output=True, env=env)
    if raise_on_non_zero_code:
        completed_process.check_returncode()
    return completed_process
