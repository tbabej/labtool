#! /bin/bash

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Install the dependencies
sudo yum install bind-dyndb-ldap bash-completion -y

# Install the IPA server
sudo ipa-server-install -U -r $DOMAIN  -p $PASSWORD  -a $PASSWORD --setup-dns --no-forwarders

# Add localhost as a name server and disable rewrites
sudo sed -i "1inameserver 127.0.0.1" /etc/resolv.conf
sudo chattr +i /etc/resolv.conf
