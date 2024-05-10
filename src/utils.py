import os
import subprocess
import sys


def run_command(cmd, return_output=False, verbose=False):
    if verbose:
        print(f"Running command {cmd}\n")

    split_cmd = cmd.split()

    process = subprocess.Popen(
        split_cmd,
        # trunk-ignore(bandit/B603)
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    output, error = process.communicate()

    if process.returncode != 0:
        error_message = (
            f"Failed to execute the command: {cmd}.\nError: {error.decode()}"
        )
        raise Exception(error_message)

    return output.decode() if return_output else None


def get_and_require_env_var(env_var_name):
    env_var = os.environ.get(env_var_name)
    if not env_var:
        print(f"Environment variable {env_var_name} was not found - exiting.")
        sys.exit(1)
    return env_var


def get_bool_from_string(bool_string):
    if not bool_string:
        return False

    if bool_string == "true":
        return True

    try:
        bool_as_int = int(bool_string)
        return bool_as_int > 0
    except ValueError:
        return False
