#!/bin/bash

# Runs the tests.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Set IPA_DIR and DIST_DIR if given via command line
if [[ $1 == "local" ]]
then
  IPA_DIR=~/dev/freeipa
fi

pushd $IPA_DIR

# Run the tests
ipa-run-tests -k 'not test_integration'
