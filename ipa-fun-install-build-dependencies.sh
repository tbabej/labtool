#!/bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Install the build dependencies.
#
# Usage: $0 <branch>
# Returns: 0 on success, 1 on failure
##############################################################################

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

set -e

pushd $IPA_DIR

sudo $DNF builddep -y --spec freeipa.spec.in

popd
