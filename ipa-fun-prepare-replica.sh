#!/bin/bash

# Prepares the replica file.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Check if hostname of VM was given
if [[ $1 == "" ]]
then
  echo "Usage: $0 vm-xyz (first segment of replica's hostname)"
fi

# $1 should be vm-xyz
REPLICA=$1.$DOMAIN
VM_ID=`echo $1 | cut -d- -f2`
REPLICA_IP=`echo $IP | cut -d. -f1-3`.`echo $VM_ID | sed 's/0*//'`

# TODO: make sure named service is started

sudo ipa-replica-prepare -p $PASSWORD --ip-address $REPLICA_IP $REPLICA
sudo mv /var/lib/ipa/replica-info-$REPLICA.gpg $REPLICA_DIR/
