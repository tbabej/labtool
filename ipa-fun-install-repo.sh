#!/bin/bash

# Sets the hostname to become subdomain of AD.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

if [[ $PLATFORM_NAME == "Fedora" ]]
then
  sudo yum install freeipa-server freeipa-client freeipa-server-trust-ad --enablerepo=updates-testing -y
elif [[ $PLATFORM_NAME == "RHEL" ]]
then
  sudo yum install ipa-server ipa-client freeipa-server-trust-ad --enablerepo=updates-testing -y
else
  echo 'Unknown platform : $PLATFORM'
fi
