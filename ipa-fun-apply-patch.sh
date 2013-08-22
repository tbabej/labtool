#! /bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
# This script applies patch that contains a given unique substring in its name.
#
# Usage: $0 <clue>
# Returns: 0 if there exists only one patch with given clue and patch applied
#          successufully
#          1 if no clue was given
#          2 if there exists unappropriate number of patches corresponding to
#            the given clue (meaning less or more than one)
##############################################################################

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Validate patch name
if [[ $1 == "" ]]
then
  # Wrong usage, print help message and exit
  echo "Usage: $0 patch_number"
  exit 1
else
  # ipa-fun-get-patch-name outputs the patch's name or the number of the patches
  # matching the clue, in case this number is not one
  MATCHES=`$DIR/ipa-fun-get-patch-name.sh $1`

  # Is there only one patch?
  if [[ ! $? == 0 ]]
  then
    # Output the number of the patches in case of error
    echo $MATCHES
    exit 2
  else
    # Success
    PATCH=$MATCHES
  fi

fi

# Exception exist set now, because ipa-fun-get-patch-name
# does not always return 0
set -e

pushd $IPA_DIR

#TODO: Check whether the $PATCH starts with > and if so, correct it

# Apply the patch
echo "Applying the patch $PATCH."
git am $PATCH 2>&1

popd
