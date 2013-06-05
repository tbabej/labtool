#! /bin/bash

# Builds the FreeIPA rpms from sources.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

if [[ ! $1 == "" ]]
then
  if [[ ! -d $WORKING_DIR/$1 ]]
  then
    echo "$WORKING_DIR/$1 does not exist"
    exit 1
  fi

  DIST_DIR=$WORKING_DIR/$1/dist
fi

if [[ -d $DIST_DIR ]]
then
  sudo rm -rf $DIST_DIR
fi

mkdir $DIST_DIR

pushd $IPA_DIR

# Build can fail if the logged user does not have access to some files
# This can happen if you played around with root in your home directory
sudo chown -R `whoami` .

# Build ALL the rpms
rm -f $DIST_DIR/freeipa*
rm -f dist/rpms/freeipa*
make -s all rpms 2>&1

# Copy the result into DIST_DIR
cp $IPA_DIR/dist/rpms/freeipa* $DIST_DIR/

popd

