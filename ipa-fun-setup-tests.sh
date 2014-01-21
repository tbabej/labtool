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
sudo cp /etc/httpd/alias/*.db /home/$USER/.ipa/alias/
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
#in_tree=True
EOF

sudo service httpd restart

sudo echo "$PASSWORD" | kinit admin

if [ -z "`rpm -qa | grep python-nose`" ]
then
	sudo yum -y install python-nose
fi

sudo chown -R $USER:$USER /home/$USER/.ipa
