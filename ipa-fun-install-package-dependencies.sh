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

# Installs dependencies for the FreeIPA packages
$DNF install -y --enablerepo='*updates-testing' 'freeipa-*' 'bash-completion'
$DNF remove -y --setopt=clean_requirements_on_remove=false 'freeipa-*'
