#!/bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Install the dependnecies for the FreeIPA packages. Use in templates to
# improve performance of the yum update.
#
# Usage: $0 <branch>
# Returns: 0 on success, 1 on failure
##############################################################################


# TODO: support other platforms

PACKAGES="freeipa-server freeipa-server-trust-ad freeipa-tests freeipa-admintools freeipa-client freeipa-python"
PACKAGES_GREP="freeipa-server|freeipa-server-trust-ad|freeipa-tests|freeipa-admintools|freeipa-client|freeipa-python"

# Installs only the dependencies for the FreeIPA packages
yum deplist $PACKAGES | grep provider | awk '{print $2}' | sort | uniq | grep -v $PACKAGES_GREP | sed ':a;N;$!ba;s/\n/ /g' | xargs yum -y install