#!/bin/bash

set -eu -o pipefail

BRANCH="$(git branch --show-current)"

if ! [[ "${BRANCH}" = "develop" ]]
then
  echo ERROR: This is not the main branch!
  exit 1
fi

NEW_VERSION="$(bump-my-version show new_version --increment release | sed -Ene 's/^([[:digit:]]+\.[[:digit:]]+)\.[[:digit:]]+$/\1/p')"

if [[ -z "${NEW_VERSION}" ]]
then
  echo ERROR: Could not parse new version.
  exit 1
fi

NEW_BRANCH="RELEASE-${NEW_VERSION}"

git branch "${NEW_BRANCH}"

bump-my-version bump minor --commit --message $'Bump version to {new_version}' --allow-dirty

git push origin "${NEW_BRANCH}"

if [ "${GITHUB_ENV:-}" ]
then
  echo "NEW_BRANCH=${NEW_BRANCH}" >> "${GITHUB_ENV}"
fi
