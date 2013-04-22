#!/bin/bash

# Sets the hostname to become subdomain of AD.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

SUBDOMAIN=.dom$ID

# Check if subdomain was given as a option
if [[ ! $1 == "" ]]
then
  ID_DOMAIN=`echo $1 | cut -d- -f2`
  SUBDOMAIN=.dom$ID_DOMAIN
fi

# Set the hostname to become subdomain of tbad
if [[ `hostname | grep tbad` == '' ]]
then
  HOSTNAME=vm-${ID}${SUBDOMAIN}.tbad.$DOMAIN
  sudo hostname $HOSTNAME
  echo "HOSTNAME=$HOSTNAME" | sudo tee -a /etc/sysconfig/network
  echo "$IP $HOSTNAME $VM" | sudo tee -a /etc/hosts
  sudo service network restart
  sudo ip -6 addr del $IP6 dev eth0
fi
