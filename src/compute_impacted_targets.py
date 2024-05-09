import os
import sys

from utils import run_command

verbose = os.environ.get("VERBOSE") == "true"

def log_if_verbose(log):
    if verbose:
        print(log)

nx_workspace_path = os.environ.get("WORKSPACE_PATH")
if nx_workspace_path:
    run_command(f"cd {nx_workspace_path}")

ls_output = run_command("ls -la", return_output=True)
print(ls_output)

current_dir = run_command("pwd", return_output=True)
print(current_dir)

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

run_command(f"npx nx graph --base={merge_instance_branch_head_sha} --head={pr_branch_head_sha} --file={affected_json_out}", verbose=verbose)

affected_json = run_command(f"cat {affected_json_out}", return_output=True)
print(affected_json)

# Output Files
impacted_projects_out=f"./impacted_projects_{pr_branch_head_sha}"
run_command(f"cmd '{affected_json_out}' | jq -r '.affectedProjects[] | select(length > 0)' >> '${impacted_projects_out}'")

num_impacted_projects=run_command(f"wc -l < '{impacted_projects_out}'", return_output=True)
print(f"Computed {num_impacted_projects} projects for sha {pr_branch_head_sha}")

print("To replicate this command, run the following")
print(f"npx nx graph --verbose --affected --base='{merge_instance_branch_head_sha}' --head='{pr_branch_head_sha}' --file='${affected_json_out}'")

impacted_projects = run_command("cat '${impacted_projects_out}'", return_output=True)
print(impacted_projects)

# Outputs
github_output = f"impacted_projects_out={impacted_projects_out}\n"
log_if_verbose(f"Setting these outputs:\n{github_output}")

with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
    f.write(github_output)
