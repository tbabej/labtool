#!/bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Detects whether the IPA developement workspace exists
#
# Usage: $0
# Returns: 0 if it exists, 1 if not
##############################################################################


# Load the configuration
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

if [ -d $IPA_DIR ]
then
  exit 0;
else
  exit 1;
fi
