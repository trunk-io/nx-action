import json
import os
import sys
import time

import requests

from utils import get_and_require_env_var, get_bool_from_string

MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 2

verbose = get_bool_from_string(os.environ.get("VERBOSE"))

IMPACTS_ALL_KEYWORD = "ALL"


def log_if_verbose(log=""):
    if verbose:
        print(log)


is_fork = get_bool_from_string(os.environ.get("IS_FORK"))
actor = get_and_require_env_var("ACTOR")

# PRs originating from a forked repo are handled differently when uploading impacted targets.
# https://docs.trunk.io/merge/set-up-trunk-merge/impacted-targets#impacted-targets-for-forked-prs
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

if len(repository_parts) != 2:
    print(f"REPOSITORY {repository} is malformed - there should only be one '/' ")
    sys.exit(1)

repo_owner = repository_parts[0]
repo_name = repository_parts[1]

pr_number = get_and_require_env_var("PR_NUMBER")
pr_branch_head_sha = get_and_require_env_var("PR_BRANCH_HEAD_SHA")

IMPACTED_TARGETS: str | list[str] = ""
impacts_all_detected = get_bool_from_string(
    get_and_require_env_var("IMPACTS_ALL_DETECTED")
)
if impacts_all_detected:
    IMPACTED_TARGETS = IMPACTS_ALL_KEYWORD
else:
    impacted_targets_file = get_and_require_env_var("IMPACTED_TARGETS_FILE")
    with open(impacted_targets_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            IMPACTED_TARGETS = []
        else:
            IMPACTED_TARGETS = content.split("\n")

log_if_verbose(f"Read impacted targets: {IMPACTED_TARGETS}")

API_URL = os.environ.get("API_URL")
if not API_URL:
    API_URL = "https://api.trunk.io:443/v1/setImpactedTargets"

data = {
    "repo": {"host": "github.com", "owner": repo_owner, "name": repo_name},
    "pr": {"number": pr_number, "sha": pr_branch_head_sha},
    "targetBranch": target_branch,
    "impactedTargets": IMPACTED_TARGETS,
}

log_if_verbose(f"Sending request body\n{data}\n")


def is_retryable_status(status_code: int) -> bool:
    return status_code >= 500


def make_request():
    return requests.post(
        API_URL,
        data=json.dumps(data),
        headers={
            "Content-Type": "application/json",
            "x-api-token": api_token if api_token else "",
            "x-forked-workflow-run-id": run_id if run_id else "",
        },
        timeout=30,
    )


resp = None
last_exception = None

for attempt in range(MAX_RETRIES + 1):
    try:
        resp = make_request()
        if not is_retryable_status(resp.status_code):
            break
        if attempt < MAX_RETRIES:
            backoff = INITIAL_BACKOFF_SECONDS * (2**attempt)
            log_if_verbose(
                f"Received {resp.status_code}, retrying in {backoff}s (attempt {attempt + 1}/{MAX_RETRIES + 1})"
            )
            time.sleep(backoff)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        last_exception = e
        if attempt < MAX_RETRIES:
            backoff = INITIAL_BACKOFF_SECONDS * (2**attempt)
            log_if_verbose(
                f"Request failed with {type(e).__name__}, retrying in {backoff}s (attempt {attempt + 1}/{MAX_RETRIES + 1})"
            )
            time.sleep(backoff)

if resp is None:
    error_type = type(last_exception).__name__ if last_exception else "Unknown error"
    print(
        f"Upload impacted targets failed after {MAX_RETRIES + 1} attempts ({error_type}). To resolve, re-run this job."
    )
    sys.exit(1)

status_code = resp.status_code

EXIT_MESSAGE = ""
EXIT_CODE = 0
if status_code == 200:
    SUCCESS_MESSAGE = ""
    if IMPACTED_TARGETS == IMPACTS_ALL_KEYWORD:
        SUCCESS_MESSAGE = "✨ Marked as impacting all other pull requests"
    else:
        SUCCESS_MESSAGE = f"✨ Uploaded {len(IMPACTED_TARGETS)} impacted targets"

    EXIT_MESSAGE = f"{SUCCESS_MESSAGE} for {pr_number} @ {pr_branch_head_sha}"
else:
    EXIT_CODE = 1

    if status_code == 401:
        if actor == "dependabot[bot]":
            EXIT_MESSAGE = "❌ Unable to upload impacted targets. Did you update your Dependabot secrets with your repo's token? See https://docs.github.com/en/code-security/dependabot/working-with-dependabot/automating-dependabot-with-github-actions#accessing-secrets for more details.\n"
        elif actor.endswith("[bot]"):
            EXIT_MESSAGE = "❌ Unable to upload impacted targets. Please verify that this bot has access to your repo's token.\n"
    else:
        EXIT_MESSAGE = f"❌ Unable to upload impacted targets. Encountered {status_code} @ {pr_branch_head_sha}. Please contact us at slack.trunk.io."

print(EXIT_MESSAGE)
if status_code != 200:
    print(f"Response body:\n{resp.text}")


sys.exit(EXIT_CODE)
