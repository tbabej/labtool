#!/bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Install the dependencies for the FreeIPA packages. Use in templates to
# improve performance of the dnf update.
#
# Usage: $0 <branch>
# Returns: 0 on success, 1 on failure
##############################################################################

# Load the configuration
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

PACKAGES="freeipa-server freeipa-server-trust-ad freeipa-tests freeipa-admintools freeipa-client freeipa-python"
PACKAGES_GREP="freeipa-server|freeipa-server-trust-ad|freeipa-tests|freeipa-admintools|freeipa-client|freeipa-python"

# Installs only the dependencies for the FreeIPA packages
#select only providers (input: "dependency: sssd >= 1.11.1\n  provider: sssd.x86_64 1.11.3-1.fc20")
$DNF deplist $PACKAGES | grep provider | \
    # select only package name (input: "provider: sssd.x86_64 1.11.3-1.fc20")
    awk '{print $2}' | \
    # cut architecture from the end (input: "sssd.x86_64")
    sed 's/\.[^.]*$//' | \
    sort | uniq | \
    # omit ipa packages
    grep -v -E "($PACKAGES_GREP)" | \
    sed ':a;N;$!ba;s/\n/ /g' | xargs sudo $DNF -y install

# Install the non-direct dependencies
sudo $DNF install --enablerepo='*updates-testing' bind-dyndb-ldap bash-completion -y
