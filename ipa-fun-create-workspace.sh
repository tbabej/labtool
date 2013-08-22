#!/bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Creates workspace for the IPA developement and all the other
#
# Usage: $0
# Returns: 0 on success, 1 on failure
##############################################################################


# Load the configuration
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

function recreate_dir(){
# mkdir -p creates directory only if it does not exist
  sudo rm -rf $1
  sudo mkdir -p $1
  sudo chown -R $USER $1
}

GIT_PATH=git://git.fedorahosted.org/git/freeipa.git
GIT_PATH_BACKUP=https://github.com/encukou/freeipa.git

# Create working dir directory structure
recreate_dir $WORKING_DIR
recreate_dir $DIST_DIR
recreate_dir $PATCH_DIR
recreate_dir $LOG_DIR

pushd $WORKING_DIR

# Remove any remnants of previous repositories
rm -rf freeipa

# Clone FreeIPA so we have our own sandbox to play in
git clone $GIT_PATH

# If the cloning fails for whatever reason, fall back to the backup
if [[ $? != 0 ]]
then
  rm -rf freeipa
  git clone $GIT_PATH_BACKUP
fi

# TODO: configure for the local repos

popd

