#!/bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Install FreeIPA packages from the repositories.
#
# Usage: $0 <branch>
# Returns: 0 on success, 1 on failure
##############################################################################

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh
set -e

# Install the packages based on the platform
# TODO: is freeipa-server-trust-ad on RHEL called the same?
# TODO: global option for using the updates-testing repository in installs?
if [[ $PLATFORM_NAME == "Fedora" ]]
then
  sudo dnf install freeipa-server freeipa-client freeipa-server-trust-ad -y
elif [[ $PLATFORM_NAME == "RHEL" ]]
then
  sudo dnf install ipa-server ipa-client freeipa-server-trust-ad -y
else
  echo 'Unknown platform : $PLATFORM'
fi
