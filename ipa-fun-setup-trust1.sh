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

# Install support for trusts
sudo ipa-adtrust-install --netbios-name=$NETBIOS -a $PASSWORD --add-sids

# Configure DNS only if on master
if [[ $1 == '' ]]
then
  ipa dnszone-add $AD_DOMAIN --name-server=advm.$AD_DOMAIN --admin-email="hostmaster@$AD_DOMAIN.com" --force --forwarder=$AD_IP --forward-policy=only --ip-address=$AD_IP
fi
