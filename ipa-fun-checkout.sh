#! /bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Checks out the sources to the given branch name.
#
# Usage: $0 <branch>
# Returns: 0 on success, 1 on failure
##############################################################################

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Validate branch name
# TODO: support just pieces of branch name
if [[ $1 == "" ]]
then
  echo "Usage: $0 branch "
  exit 1
fi

bash $DIR/ipa-fun-enable-repos.sh

pushd $IPA_DIR

# Checkout to the given branch
echo "Checking out ot the branch $1"
git checkout $1

popd
