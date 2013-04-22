#!/bin/bash

# Performs after-boot configuration.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Make sure that resolv.conf contains localhost
if [[ `cat /etc/resolv.conf | grep $IP` == '' ]]
then
  sudo sed -i.bak "2a\nameserver $IP" /etc/resolv.conf
fi

echo $PASSWORD | kinit admin

# Add the trust
echo $AD_PASSWORD | ipa trust-add --type=ad $AD_DOMAIN --admin Administrator --password
