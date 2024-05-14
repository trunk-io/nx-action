#!/usr/bin/env bash

set -euo pipefail

if [[ -z ${MAJOR_VERSION} ]]; then
	echo "Missing major version to tag release as"
	exit 1
fi

if [[ -z ${RELEASE_TARGET} ]]; then
	echo "Missing release target"
	exit 1
fi

git config user.name trunkio
git config user.email github-actions@trunk.io
git tag -f "${MAJOR_VERSION}" "${RELEASE_TARGET}"
git push origin "${MAJOR_VERSION}" --force
