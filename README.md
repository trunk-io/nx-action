# merge-action

Hosts the code for the [Trunk Merge Queue](https://docs.trunk.io/merge-queue) GitHub Action, which
makes it easy to upload the required impacted targets for PRs when running your merge queues in
["Parallel" mode](https://docs.trunk.io/merge-queue/parallel-queues). Currently, this action
supports the [Nx](https://nx.dev/) build system

## Overview

Trunk Merge Queue checks and tests all PRs before they merge, guaranteeing that the branches you
care about the most will always pass all tests. Trunk's Merge Queues, unlike traditional merge
queues, can run in "Parallel" mode, which increases throughput by dynamically creating merge queues
for pull requests that affect different parts of your codebase instead of testing them all together.
That means no more waiting for your backend changes to test before landing your doc changes!

Running in "Parallel" mode requires providing Trunk Merge with the list of
[impacted targets](https://docs.trunk.io/merge-queue/parallel-queues#:~:text=What%20are%20Impacted%20Targets%3F)
resulting from the changes in your PR. If using a supported build system, this action can take care
of getting that list and sending it to Trunk Merge.

If you do not already have one for your repo, a Trunk Merge Queue can be created at
[app.trunk.io](https://app.trunk.io). Documentation on how to do that can be found
[here](https://docs.trunk.io/merge-queue/set-up-trunk-merge).

### How This Action Works

When run on a pull request, the merge action will compare the merge commit of your PR + the base
branch to the tip of the PR's base branch. With those two commits, we'll query your build system to
get the list of targets that were impacted directly due to the PR's code changes. That list will
then be uploaded to Trunk Merge Queue. This way, when running in "Parallel" mode, Trunk Merge Queue
will create merge queues just for the PRs that share any impacted targets, only testing PRs that
actually can impact one-another against each other.

Marking a PR as impacting every single other PR is also possible using the `impact-all-filters-path`
argument for the action. This is useful for if a PR contains a change that any PRs queued in the
future should also depend on - an example would be PRs that introduce or change workflows run on
every PR.

Sending this list of impacted targets for your PR is required before it can be queued when running
in "Parallel" mode. If you
[queue your PR](https://docs.trunk.io/merge-queue/set-up-trunk-merge#submit-pull-requests) before
the action uploads the list, the PR will wait until the list has been uploaded before being queued.

## Usage

Running this action in a GitHub workflow will require you knowing your Trunk Repo or Trunk Org API
token.

### Example

An example of how this action would be run in a GitHub workflow is below.

<!-- start usage -->

```yaml
name: Upload Impacted Targets
on: pull_request

jobs:
  compute_impacted_targets:
    name: Compute Impacted Targets
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Compute Impacted Targets
        uses: trunk-io/nx-action@v1
        with:
          # Use your Trunk repo or org API token to authenticate impacted targets uploads.
          # This secret should be provided as a GitHub secret.
          # See https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions.
          trunk-token: ${{ secrets.TRUNK_API_TOKEN }}
```

<!-- end usage -->

For more information on each possible argument you can provide, see
[action.yaml](https://github.com/trunk-io/nx-action/blob/main/action.yaml)

### Tests

To run tests:

```bash
pnpm install
pnpm test
```

## What is an Impacted Target?

An impacted target is a unit that is affected by a particular PR. For example (using Bazel), a
change at `src/backend/app` will impact the Bazel `src/backend` package. Any two pull requests that
share an impacted target must be tested together; otherwise, they can be tested independently.

## Under the hood

We use the Nx CLI to create a dependency graph that shows all of the affected libraries from the
pull request. More information on the command can be found
[here](https://nx.dev/nx-api/nx/documents/dep-graph)

## Questions

For any questions, contact us on [Slack](https://slack.trunk.io).
