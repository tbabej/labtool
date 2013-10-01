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

# Fix the time issues
sudo systemctl stop ntpd
sudo systemctl disable ntpd
sudo ntpdate advm.$AD_DOMAIN

# Obtain admin credentials
echo $PASSWORD | kinit admin

# Install support for trusts
sudo ipa-adtrust-install --netbios-name=$NETBIOS -a $PASSWORD --add-sids -U

# Configure DNS only if on master
if [[ $1 == '' ]]
then
  ipa dnszone-add $AD_DOMAIN --name-server=advm.$AD_DOMAIN --admin-email="hostmaster@$AD_DOMAIN.com" --force --forwarder=$AD_IP --forward-policy=only --ip-address=$AD_IP
fi

# Make sure that resolv.conf contains localhost
if [[ `cat /etc/resolv.conf | grep $IP` == '' ]]
then
  sudo sed -i.bak "2a\nameserver $IP" /etc/resolv.conf
fi

echo $PASSWORD | kinit admin

# Add the trust
echo $AD_PASSWORD | ipa trust-add --type=ad $AD_DOMAIN --admin Administrator --password
