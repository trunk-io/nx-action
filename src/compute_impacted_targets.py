import os

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


PACKAGE_MANAGER_COMMANDS = {
    "pnpm": ("pnpm install --no-frozen-lockfile", "pnpm exec nx"),
    "yarn": ("yarn install --force", "yarn exec nx"),
    "npm": ("npm install --force", "npx nx"),
}


def detect_package_manager():
    # PACKAGE_MANAGER env var overrides lock file detection.
    override = os.environ.get("PACKAGE_MANAGER", "").strip().lower()
    if override:
        if override not in PACKAGE_MANAGER_COMMANDS:
            raise ValueError(
                f"Unsupported PACKAGE_MANAGER: {override}. "
                f"Expected one of: {', '.join(PACKAGE_MANAGER_COMMANDS)}."
            )
        return override
    if os.path.isfile("pnpm-lock.yaml"):
        return "pnpm"
    if os.path.isfile("yarn.lock"):
        return "yarn"
    return "npm"


# A caller may provide its own Nx (for example a shim installed outside the
# workspace node_modules). Computing impacted targets reads the project graph,
# not installed dependencies, so no package manager install is needed then.
nx_bin = os.environ.get("NX_BIN", "").strip()
if nx_bin:
    nx_prefix = nx_bin
    log_if_verbose(f"Using provided Nx binary: {nx_bin}. Skipping install.")
else:
    package_manager = detect_package_manager()
    install_cmd, nx_prefix = PACKAGE_MANAGER_COMMANDS[package_manager]

    # Install and build necessary Nx libs.
    if get_bool_from_string(os.environ.get("SKIP_INSTALL")):
        log_if_verbose(f"Detected package manager: {package_manager}. Skipping install.")
    else:
        log_if_verbose(f"Detected package manager, using: {install_cmd}")
        run_command(install_cmd)

merge_instance_branch = get_and_require_env_var("MERGE_INSTANCE_BRANCH")
merge_instance_branch_head_sha = get_and_require_env_var(
    "MERGE_INSTANCE_BRANCH_HEAD_SHA"
)
pr_branch_head_sha = get_and_require_env_var("PR_BRANCH_HEAD_SHA")

# Get the list of impacted targets by leveraging Nx's dependency graph capabilities.
# https://nx.dev/nx-api/nx/documents/dep-graph
affected_list_out = f"./{merge_instance_branch_head_sha}_{pr_branch_head_sha}.txt"
nx_show_command_base = f"{nx_prefix} show projects --affected --base={merge_instance_branch_head_sha} --head={pr_branch_head_sha}"
affected_output = run_command(nx_show_command_base, verbose=verbose, return_output=True)

print(f"Impacted projects are:")
print(affected_output)

affected_projects = []
if affected_output:
    affected_projects = affected_output.split("\n")

# Move this to a file so we can pass it to the next action, as this list
# can be rather large.
impacted_targets_out = f"./{merge_instance_branch_head_sha}"
with open(impacted_targets_out, "w", encoding="utf-8") as f:
    f.write(f"{affected_output}")

num_impacted_projects = len(affected_projects)
print(
    f"Computed {num_impacted_projects} impacted projects for sha {pr_branch_head_sha}"
)

print(f"To replicate this command, run the following:\n{nx_show_command_base}\n")

# Outputs
github_output = f"impacted_targets_out={impacted_targets_out}\n"
log_if_verbose(f"Setting these outputs:\n{github_output}\n")

write_to_github_output(github_output)
