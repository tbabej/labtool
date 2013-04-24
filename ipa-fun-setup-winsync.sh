#!/bin/bash

# Sets the hostname to become subdomain of AD.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Check is hostname was properly set up during IPA installation
if [[ `hostname | grep tbad` == '' ]]
then
  echo "The hostname is not properly set for auto winsync."
  exit 1
fi

# Configure DNS only if on master
if [[ $1 == '' ]]
then
  ipa dnszone-add $AD_DOMAIN --name-server=advm.$AD_DOMAIN --admin-email="hostmaster@$AD_DOMAIN.com" --force --forwarder=$AD_IP --forward-policy=only
fi

# Prepare the directory
cd /etc/openldap/
sudo rm -rf cacerts
sudo mkdir cacerts

# Download the certificates
cd cacerts
sudo wget localhost/ipa/config/ca.crt
sudo cp $AD_CERTIFICATE_PATH ./ad_cert.cer

# Rehash the certificate
sudo cacertdir_rehash /etc/openldap/cacerts/

# Write down configuration
echo "TLS_CACERTDIR /etc/openldap/cacerts/" | sudo tee -a /etc/openldap/ldap.conf
echo "TLS_REQCERT allow" | sudo tee -a /etc/openldap/ldap.conf

sudo ipa-replica-manage connect --winsync --binddn cn=Administrator,cn=Users,$BASEDN --bindpw Secret123  --passsync Secret123 --cacert /etc/openldap/cacerts/ad_cert.cer advm.$AD_DOMAIN -v
