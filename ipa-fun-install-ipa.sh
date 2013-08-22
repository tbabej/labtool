#! /bin/bash

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Install the dependencies
sudo yum install bind-dyndb-ldap bash-completion -y

# Install the IPA server
sudo ipa-server-install -U -r $DOMAIN  -p $PASSWORD  -a $PASSWORD --setup-dns --no-forwarders

# Add forwarder to be double sure

# TODO: is this necessary?
#if [[ cat /etc/resolv.conf | grep $FORWARDER == '' ]]
#then
#  echo "nameserver $FORWARDER" | sudo tee -a /etc/resolv.conf
#fi
