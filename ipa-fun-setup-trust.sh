#!/bin/bash

# Sets the hostname to become subdomain of AD.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

if [[ $1 != '' ]]
then
  NETBIOS=DOM`echo $1 | cut -d- -f2`
fi

# Obtain admin credentials
echo $PASSWORD | kinit admin

# Configure DNS only if on master
if [[ $1 == '' ]]
then
  # Check if it does not exist already, if not, configure
  set +e
  ipa dnsforwardzone-show $AD_DOMAIN
  if [[ $? != 0 ]]
  then
    ipa dnsforwardzone-add $AD_DOMAIN --forwarder=$AD_IP --forward-policy=only
  fi
  set -e
fi

# Fix the time issues
sudo systemctl stop ntpd
sudo systemctl disable ntpd
sudo ntpdate advm.$AD_DOMAIN

# Install support for trusts
sudo ipa-adtrust-install --netbios-name=$NETBIOS -a $PASSWORD --add-sids -U

# Make sure that resolv.conf contains localhost
if [[ `cat /etc/resolv.conf | grep $IP` == '' ]]
then
  sudo sed -i.bak "2a\nameserver $IP" /etc/resolv.conf
fi

echo $PASSWORD | kinit admin

# Add the trust
echo $AD_PASSWORD | ipa trust-add --type=ad $AD_DOMAIN --admin Administrator --password
