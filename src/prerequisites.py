import os
import sys

from utils import run_command

verbose = os.environ.get("VERBOSE") == "true"

def log_if_verbose(log):
    if verbose:
        print(log)

# NOTE: We cannot assume that the checked out Git repo (e.g. via actions-checkout)
# was a shallow vs a complete clone. The `--depth` options deepens the commit history
# in both clone modes: https://git-scm.com/docs/fetch-options#Documentation/fetch-options.txt---depthltdepthgt
def fetch_remote_git_history(ref):
    git_cmd = f"git fetch --quiet --depth=2147483647 origin {ref}"
    run_command(git_cmd, verbose=verbose)

# Get refs for merge instance branch and the head of the PR
pr_head_sha = os.environ.get("PR_BRANCH_HEAD_SHA")
merge_instance_branch = os.environ.get("TARGET_BRANCH")
if not merge_instance_branch:
    merge_instance_branch = os.environ.get("DEFAULT_BRANCH")

if not merge_instance_branch:
    print("No merge instance branch found. Exiting.")
    sys.exit(1)

fetch_remote_git_history(merge_instance_branch)
fetch_remote_git_history(pr_head_sha)

merge_instance_branch_head_sha=run_command(f"git rev-parse 'origin/{merge_instance_branch}'", return_output=True, verbose=verbose)
if not merge_instance_branch_head_sha:
    print("Could not identify merge instance branch head sha")
    sys.exit(1)

github_output = f"merge_instance_branch={merge_instance_branch}\nmerge_instance_branch_head_sha={merge_instance_branch_head_sha}\n"
log_if_verbose(f"Setting these outputs:\n{github_output}")

with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write(github_output)