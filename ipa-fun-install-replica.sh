#!/bin/bash

# Install the replica.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Check if hostname of VM was given
if [[ $1 == "" ]]
then
  echo "Usage: $0 vm-xyz (first segment of masters's hostname)"
fi

# Syncing time with the master server
sudo ntpdate $1

# Install the replica.
sudo ipa-replica-install -U -p $PASSWORD -w $PASSWORD --ip-address $IP $REPLICA_DIR/replica-info-$SERVER.gpg
