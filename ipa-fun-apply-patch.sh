#! /bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Validate patch name
if [[ $1 == "" ]]
then
  echo "Usage: $0 patch_number"
  exit 1
else
  MATCHES=`$DIR/ipa-fun-get-patch-name.sh $1`
  if [[ ! $? == 0 ]]
  then
    echo $MATCHES
    exit 2
  else
    PATCH=$MATCHES
  fi
fi

# Exception exist set now, because ipa-fun-get-patch-name
# does not always return 0
set -e

pushd $IPA_DIR

# Apply the patch
echo "Applying the patch $PATCH."
git am $PATCH 2>&1

popd
