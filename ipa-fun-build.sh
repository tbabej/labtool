#! /bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Builds the FreeIPA rpms from sources.
# Removes everything from the $DIST_DIR and moves newly built RPMs there
#
# Usage: $0
# Returns: 0 on success, 1 on failure
##############################################################################

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Remove everything from the $DIST_DIR, so that collision with the new RPMS
# does not happen
if [[ -d $DIST_DIR ]]
then
  rm -rf $DIST_DIR/*
  rm -rf $DIST_DIR/.*
fi

# Make sure that the directory does exist, since rm -rf supresses errors
mkdir -p $DIST_DIR

# We checkout to the directory with the sources
pushd $IPA_DIR

# Build can fail if the logged user does not have access to some files
# This can happen if you played around with root in your home directory
sudo chown -R $USER .

# Make sure there is no garbage in the dist directory
sudo rm -rf dist/*

# Build ALL the rpms
make -s all rpms 2>&1

# Copy the result into DIST_DIR
cp dist/rpms/freeipa* $DIST_DIR/

popd

