#! /bin/bash

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Add localhost as a name server, installer needs hostname resolvable
sudo chattr -i /etc/resolv.conf
sudo sed -i "1inameserver 127.0.0.1" /etc/resolv.conf

# Install the IPA server
sudo ipa-server-install -U -r $DOMAIN  -p $PASSWORD  -a $PASSWORD --setup-dns --no-forwarders
