#!/bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Sets the hostname properly.
#
# Usage: $0 <hostname>
# Returns: 0 on success, 1 on failure
##############################################################################

# If any command here fails, exit the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh
set -e

if [[ $1 == '' ]]
then
  echo 'Usage: $0 <hostname>'
  exit 1
fi

HOSTNAME=$1
HOSTNAME_SHORT=`echo $1 | cut -d. -f1`

# Remove IPv6 if we are going for trusts
if [[ `echo $HOSTNAME | grep tbad` == '' ]]
then
  sudo ip -6 addr del $IP6 dev eth0
fi

sudo hostname $HOSTNAME
echo "$HOSTNAME" | sudo tee /etc/hostname
echo "HOSTNAME=$HOSTNAME" | sudo tee -a /etc/sysconfig/network
echo "$IP $HOSTNAME $HOSTNAME_SHORT" | sudo tee -a /etc/hosts
