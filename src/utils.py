import subprocess

def run_command(cmd, return_output=False, verbose=False):
    if verbose:
        print(f"Running command {cmd}")

    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if process.returncode != 0:
        error_message = f"Failed to execute the command: {cmd}.\nError: {error.decode()}"
        raise Exception(error_message)

    return output.decode() if return_output else None