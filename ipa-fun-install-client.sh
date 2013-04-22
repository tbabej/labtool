#!/bin/bash

# Install the client.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Check if hostname of master was given
if [[ $1 == "" ]]
then
  echo "Usage: $0 vm-xyz (first segment of masters's hostname)"
fi

# TODO: support client installation options

# Install the client.
sudo ipa-client-install --server $1.$DOMAIN --domain $DOMAIN -p admin -w $PASSWORD -U
