#!/usr/bin/env bash
# Tests src/scripts/upload_impacted_targets_github_actions.sh against a stub `trunk` that records its argv.
set -uo pipefail

script="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/src/scripts/upload_impacted_targets_github_actions.sh"
dir=$(mktemp -d)
trap 'rm -rf "${dir}"' EXIT
argv_file="${dir}/argv"
failures=0

stub_trunk() {
	printf '#!/usr/bin/env bash\n%s\n' "$1" >"${dir}/trunk"
	chmod +x "${dir}/trunk"
}

run() {
	rm -f "${argv_file}"
	env -i PATH="${dir}:${PATH}" TARGET_BRANCH=main PR_NUMBER=123 PR_SHA=abc123 \
		IMPACTS_ALL_DETECTED=false "$@" bash "${script}" >/dev/null 2>&1
}

expect_argv() {
	local name=$1 want=$2 got
	got=$(tr '\n' ' ' <"${argv_file}" 2>/dev/null || true)
	if [[ ${got% } != "mergequeue upload-impacted-targets --target-branch main --pr 123 --sha abc123 ${want}" ]]; then
		echo "FAIL ${name}: got '${got% }'"
		failures=$((failures + 1))
	else
		echo "ok   ${name}"
	fi
}

expect_failure_without_upload() {
	local name=$1
	shift
	if run "$@" || [[ -f ${argv_file} ]]; then
		echo "FAIL ${name}: succeeded or called trunk"
		failures=$((failures + 1))
	else
		echo "ok   ${name}"
	fi
}

stub_trunk "printf '%s\\n' \"\$@\" > '${argv_file}'"

printf 'app\nlib\n' >"${dir}/targets"
run IMPACTED_TARGETS_FILE="${dir}/targets"
expect_argv "uploads the computed targets file" "--targets-file ${dir}/targets"

run IMPACTS_ALL_DETECTED=true IMPACTED_TARGETS_FILE=
expect_argv "declares every target impacted when impacts-all was detected" "--all"

printf '\n  \n' >"${dir}/empty"
run IMPACTED_TARGETS_FILE="${dir}/empty"
expect_argv "declares nothing impacted when the computation found no targets" "--none"

# A missing file is a failed computation; "impacts nothing" would satisfy the readiness gate.
expect_failure_without_upload "fails when no targets file was set" IMPACTED_TARGETS_FILE=
expect_failure_without_upload "fails when the targets file is missing" IMPACTED_TARGETS_FILE="${dir}/missing"
expect_failure_without_upload "fails when the PR number is missing" PR_NUMBER= IMPACTED_TARGETS_FILE="${dir}/targets"

stub_trunk "exit 3"
if run IMPACTED_TARGETS_FILE="${dir}/targets"; then
	echo "FAIL fails when the upload fails"
	failures=$((failures + 1))
else
	echo "ok   fails when the upload fails"
fi

exit $((failures > 0))
