import os
import sys
import json

from utils import run_command

verbose = os.environ.get("VERBOSE") == "true"

def log_if_verbose(log):
    if verbose:
        print(log)

run_command("npm install --force")

merge_instance_branch = os.environ.get("MERGE_INSTANCE_BRANCH")
if not merge_instance_branch:
    print("No merge instance branch found. Exiting.")
    sys.exit(1)

merge_instance_branch_head_sha = os.environ.get("MERGE_INSTANCE_BRANCH_HEAD_SHA")
if not merge_instance_branch_head_sha:
    print("No merge instance branch head SHA found. Exiting.")
    sys.exit(1)

pr_branch_head_sha = os.environ.get("PR_BRANCH_HEAD_SHA")
if not pr_branch_head_sha:
    print("No PR branch head SHA found. Exiting.")
    sys.exit(1)

affected_json_out=f"./{merge_instance_branch_head_sha}_{pr_branch_head_sha}.json"

nx_graph_command = f"npx nx graph --affected --verbose --base={merge_instance_branch_head_sha} --head={pr_branch_head_sha} --file={affected_json_out}"
graph_output = run_command(nx_graph_command, verbose=verbose)
log_if_verbose(graph_output)

affected_json = json.loads(run_command(f"cat {affected_json_out}", return_output=True))

impacted_projects = affected_json["affectedProjects"] if "affectedProjects" in affected_json else []
print(f"Impacted projects are:")
print(*impacted_projects, sep=", ")

num_impacted_projects=len(impacted_projects)
print(f"Computed {num_impacted_projects} projects for sha {pr_branch_head_sha}")

print(f"To replicate this command, run the following:\n{nx_graph_command}")

# Outputs
github_output = f"impacted_projects_out={json.dumps(impacted_projects)}\n"
log_if_verbose(f"Setting these outputs:\n{github_output}")

with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write(github_output)
