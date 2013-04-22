#! /bin/bash

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Validate patch name
if [[ $1 == "" ]]
then
  echo "Usage: $0 patch_number [destination]"
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

# Check if local was given as option
if [[ $2 == "local" ]]
then
  IPA_DIR=~/dev/freeipa
fi

pushd $IPA_DIR

# Apply the patch
echo "Applying the patch $PATCH."
git am $PATCH

popd
