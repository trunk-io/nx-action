import json
import os
import sys

from utils import (
    get_and_require_env_var,
    get_bool_from_string,
    run_command,
    write_to_github_output,
)

verbose = get_bool_from_string(os.environ.get("VERBOSE"))


def log_if_verbose(log=""):
    if verbose:
        print(log)


# NOTE: We cannot assume that the checked out Git repo (e.g. via actions-checkout)
# was a shallow vs a complete clone. The `--depth` options deepens the commit history
# in both clone modes: https://git-scm.com/docs/fetch-options#Documentation/fetch-options.txt---depthltdepthgt
def fetch_remote_git_history(ref):
    git_cmd = f"git fetch --quiet --depth=2147483647 origin {ref}"
    run_command(git_cmd, verbose=verbose)


# Get refs for merge instance branch and the head of the PR
pr_head_sha = get_and_require_env_var("PR_BRANCH_HEAD_SHA")
merge_instance_branch = os.environ.get("TARGET_BRANCH")
if not merge_instance_branch:
    merge_instance_branch = get_and_require_env_var("DEFAULT_BRANCH")

if not merge_instance_branch:
    print("No merge instance branch found. Exiting.")
    sys.exit(1)

# Check if any file specified by the filters in impact-all-filters-path was
# changed in the PR. If it was, then mark this PR as impacting all other PRs.
impacts_filters_changes = os.environ.get("IMPACTS_FILTERS_CHANGES")
if impacts_filters_changes:
    changes_count = len(json.loads(impacts_filters_changes))
    if changes_count:
        log_if_verbose(
            "Skipping remaining prerequisite steps, as this PR will be marked as impacting all other PRs"
        )
        write_to_github_output("impacts_all_detected=true")
        sys.exit(0)

fetch_remote_git_history(merge_instance_branch)
fetch_remote_git_history(pr_head_sha)

merge_instance_branch_head_sha = run_command(
    f"git rev-parse origin/{merge_instance_branch}",
    return_output=True,
    verbose=verbose,
)
if not merge_instance_branch_head_sha:
    print("Could not identify merge instance branch head sha")
    sys.exit(1)

github_output = f"merge_instance_branch={merge_instance_branch}\nmerge_instance_branch_head_sha={merge_instance_branch_head_sha}\nimpacts_all_detected=false"
log_if_verbose(f"Setting these outputs:\n{github_output}")

write_to_github_output(github_output)
