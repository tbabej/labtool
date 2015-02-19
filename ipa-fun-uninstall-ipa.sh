#!/bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Uninstalls the FreeIPA packages and server.
#
# Usage: $0
# Returns: 0 on success, 1 on failure
##############################################################################

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh
set -e


# In case there are already packages, make sure there is no debris left
if [[ `rpm -qa | grep ipa-server` != '' ]]
then
  sudo ipa-server-install --uninstall -U
  sudo ipa-server-install --uninstall -U
  sudo ipa-server-install --uninstall -U
  sudo pkidestroy -s CA -i pki-tomcat
  sudo rm -rf /var/log/pki/pki-tomcat
  sudo rm -rf /etc/sysconfig/pki-tomcat
  sudo rm -rf /etc/sysconfig/pki/tomcat/pki-tomcat
  sudo rm -rf /var/lib/pki/pki-tomcat
  sudo rm -rf /etc/pki/pki-tomcat
  sudo dnf remove freeipa-* -y
fi
