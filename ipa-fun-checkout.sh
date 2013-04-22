#! /bin/bash

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Validate branch name
# TODO: support just pieces of branch name
if [[ $1 == "" ]]
then
  echo "Usage: $0 branch [destination]"
  exit 1
fi

# Check if destination was given as option
if [[ $2 == "local" ]]
then
  IPA_DIR=~/dev/freeipa
fi

pushd $IPA_DIR

# Checkout to the given branch
echo "Checking out ot the branch $1"
git checkout $1

popd
