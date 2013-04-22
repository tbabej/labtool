#! /bin/bash

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

sudo ipa-server-install -U -r $DOMAIN  -p $PASSWORD  -a $PASSWORD --setup-dns --forwarder=$FORWARDER

# Restart the named service and add forwarder to be double sure
sudo service named restart
echo "nameserver $FORWARDER" | sudo tee -a /etc/resolv.conf
