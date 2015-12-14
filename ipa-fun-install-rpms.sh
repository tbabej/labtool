#! /bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Installs the FreeIPA packages from sources.
#
# Usage: $0
# Returns: 0 on success, 1 on failure
##############################################################################

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh
set -e


pushd $DIST_DIR
sudo $DNF install ./* -y
popd

