#!/bin/bash

# Sets up necessary configuration for tests to run.

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

if [ ! -f /etc/ipa/default.conf ]
then
	echo "Missing /etc/ipa/default.conf file"
	exit 1
fi

sudo sed -ri 's/KrbMethodK5Passwd off/KrbMethodK5Passwd on/' /etc/httpd/conf.d/ipa.conf

sudo rm -rf /home/$USER/.ipa/alias
mkdir -p /home/$USER/.ipa/alias

sudo echo $PASSWORD > /home/$USER/.ipa/.dmpw

rm -rf /home/$USER/.ipa/alias
sudo cp -r /etc/httpd/alias /home/$USER/.ipa/alias
sudo cp /etc/httpd/alias/pwdfile.txt /home/$USER/.ipa/alias/.pwd

sudo chown -R $USER /home/$USER/.ipa
sudo chgrp -R $USER /home/$USER/.ipa

sudo cat > /home/$USER/.ipa/default.conf <<EOF
[global]
basedn = $BASEDN
realm = $REALM
domain = $DOMAIN
server = $HOSTNAME
xmlrpc_uri = https://$HOSTNAME/ipa/xml
enable_ra = True
wait_for_attr = True
wait_for_dns = 10
ldap_uri=ldapi://%2fvar%2frun%2fslapd-${DOMAIN_DASHED}.socket
EOF

sudo service httpd restart

sudo echo "$PASSWORD" | kinit admin

sudo chown -R $USER:$USER /home/$USER/.ipa
