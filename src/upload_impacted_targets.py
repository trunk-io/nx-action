import ast
import os
import sys

import requests

from utils import get_and_require_env_var, get_bool_from_string, log_if_verbose

verbose = get_bool_from_string(os.environ.get("VERBOSE"))
is_fork = get_bool_from_string(os.environ.get("IS_FORK"))
actor = get_and_require_env_var("ACTOR")

api_token = os.environ.get("API_TOKEN")
if not api_token and not is_fork:
    print(
        """
No API_TOKEN was provided - it is required when the PR is not from a fork. To get your API token, follow
https://docs.trunk.io/merge/set-up-trunk-merge/merge-+-bazel#set-up-the-github-action
"""
    )
    sys.exit(1)

run_id = os.environ.get("RUN_ID")
if not run_id and is_fork:
    print("No RUN_ID was provided - it is required when the PR is from a fork")
    sys.exit(1)

target_branch = get_and_require_env_var("MERGE_INSTANCE_BRANCH")
repository = get_and_require_env_var("REPOSITORY")
repository_parts = repository.split("/")

if len(repository_parts):
    print(f"REPOSITORY {repository} is malformed - there should only be one '/' ")
    sys.exit(1)

repo_owner = repository_parts[0]
repo_name = repository_parts[1]

pr_number = get_and_require_env_var("PR_NUMBER")
pr_branch_head_sha = get_and_require_env_var("PR_BRANCH_HEAD_SHA")

impacted_targets_file = get_and_require_env_var("IMPACTED_TARGETS_FILE")
with open(impacted_targets_file, "r", encoding="utf-8") as f:
    impacted_targets = f.read()

impacted_targets = ast.literal_eval(impacted_targets)

log_if_verbose(f"Read impacted targets: {impacted_targets}")

api_url = os.environ.get("API_URL")
if not api_url:
    # trunk-ignore(pylint/C0103)
    api_url = "https://api.trunk.io:443/v1/setImpactedTargets"

data = {
    "repo": {"host": "github.com", "owner": repo_owner, "name": repo_name},
    "pr": {"number": pr_number, "sha": pr_branch_head_sha},
    "targetBranch": target_branch,
    "impactedTargets": impacted_targets,
}

log_if_verbose(f"Sending request body\n{data}\n")

try:
    resp = requests.post(
        api_url,
        data,
        headers={
            "Content-Type": "application/json",
            "x-api-token": api_token if api_token else "",
            "x-forked-workflow-run-id": run_id if run_id else "",
        },
        timeout=15,
    )
except requests.exceptions.Timeout:
    print("Request to upload impacted targets timed out")

status_code = resp.status_code
EXIT_CODE = 0
if status_code == 200:
    print(
        f"✨ Uploaded {len(impacted_targets)} impacted targets for {pr_number} @ {pr_branch_head_sha}"
    )
else:
    EXIT_CODE = 1

    if status_code == 401:
        if actor == "dependabot[bot]":
            print(
                "❌ Unable to upload impacted targets. Did you update your Dependabot secrets with your repo's token? See https://docs.github.com/en/code-security/dependabot/working-with-dependabot/automating-dependabot-with-github-actions#accessing-secrets for more details.\n"
            )
        elif actor.endswith("[bot]"):
            print(
                "❌ Unable to upload impacted targets. Please verify that this bot has access to your repo's token.\n"
            )
    print(f"Response body:\n{resp.text}")

sys.exit(EXIT_CODE)
