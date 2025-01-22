#!/bin/bash

set -eu -o pipefail

BRANCH=$(git branch --show-current)

if ! [[ "${BRANCH}" =~ ^RELEASE-[0-9]+\.[0-9]+$ ]]
then
  echo ERROR: This is not a release branch!
  exit 1
fi

NEW_VERSION="$(bump-my-version show new_version --increment release)"
echo "Release ${NEW_VERSION}"

if ! [[ "RELEASE-${NEW_VERSION}" == "${BRANCH}"* ]]
then
  echo ERROR: Version does not match release branch
  exit 1
fi

bump-my-version bump release --commit --message "Release {new_version}" --tag --tag-name "v{new_version}" --tag-message "Release {new_version}"
bump-my-version bump patch --commit

git push origin "${BRANCH}" "v${NEW_VERSION}"
