#! /bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Builds the FreeIPA rpms from sources.
# Removes everything from the $DIST_DIR and moves newly built RPMs there
#
# Usage: $0
# Returns: 0 on success, 1 on failure
##############################################################################

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Change sources in site-packages
pushd "/usr/lib/python2.7/site-packages/"

for DIR in `echo ipalib ipaserver ipapython ipatests`
do
  echo "Removing $DIR"
  sudo rm -rf $DIR || :

  echo "Linking $IPA_DIR/$DIR to $DIR"
  sudo ln -s $IPA_DIR/$DIR $DIR
done

popd; echo; echo

# Change tools
pushd $IPA_DIR/install/tools
for FILE in ipa-* ipactl
do
  FILEPATH=`which $FILE` || FILEPATH="/usr/sbin/$FILE"

  echo "Removing $FILEPATH"
  sudo rm $FILEPATH || :

  echo "Linking $IPA_DIR/install/tools/$FILE to $FILEPATH"
  sudo ln -s $IPA_DIR/install/tools/$FILE $FILEPATH
done

popd; echo; echo;

# Install share directory
sudo rm -rf /usr/share/ipa || :
sudo mkdir /usr/share/ipa

pushd $IPA_DIR/install/share
for FILE in *
do
  sudo ln -s $IPA_DIR/install/share/$FILE /usr/share/ipa/$FILE
done

for FILE in `echo ffextension html migration ui updates wsgi`
do
  sudo ln -s $IPA_DIR/install/$FILE /usr/share/ipa/$FILE
done
