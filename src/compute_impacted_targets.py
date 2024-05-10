import json
import os

from utils import get_and_require_env_var, get_bool_from_string, run_command

verbose = get_bool_from_string(os.environ.get("VERBOSE"))


def log_if_verbose(log=""):
    if verbose:
        print(log)


run_command("npm install --force")

merge_instance_branch = get_and_require_env_var("MERGE_INSTANCE_BRANCH")
merge_instance_branch_head_sha = get_and_require_env_var(
    "MERGE_INSTANCE_BRANCH_HEAD_SHA"
)
pr_branch_head_sha = get_and_require_env_var("PR_BRANCH_HEAD_SHA")

affected_json_out = f"./{merge_instance_branch_head_sha}_{pr_branch_head_sha}.json"
nx_graph_command_base = f"npx nx graph --affected --verbose --base={merge_instance_branch_head_sha} --head={pr_branch_head_sha}"
graph_output = run_command(
    f"{nx_graph_command_base} --file={affected_json_out}", verbose=verbose
)
log_if_verbose(graph_output)

affected_json = json.loads(run_command(f"cat {affected_json_out}", return_output=True))

impacted_projects = (
    affected_json["affectedProjects"] if "affectedProjects" in affected_json else []
)
print(f"Impacted projects are:")
print(*impacted_projects, sep=",\n")

# Move this to a file so we can pass it to the next action, as this list
# can be rather large.
impacted_targets_out = f"./{merge_instance_branch_head_sha}"
with open(impacted_targets_out, "w", encoding="utf-8") as f:
    f.write(f"{impacted_projects}")

num_impacted_projects = len(impacted_projects)
print(
    f"Computed {num_impacted_projects} impacted projects for sha {pr_branch_head_sha}"
)

print(f"To replicate this command, run the following:\n{nx_graph_command_base}\n")

# Outputs
github_output = f"impacted_targets_out={impacted_targets_out}\n"
log_if_verbose(f"Setting these outputs:\n{github_output}\n")

with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write(github_output)
