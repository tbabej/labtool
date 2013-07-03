#! /bin/bash

if [[ `rpm -qa | grep freeipa` != '' ]]
then
  sudo ipa-server-install --uninstall -U
  sudo pkidestroy -s CA -i pki-tomcat
  sudo rm -rf /var/log/pki/pki-tomcat
  sudo rm -rf /etc/sysconfig/pki-tomcat
  sudo rm -rf /etc/sysconfig/pki/tomcat/pki-tomcat
  sudo rm -rf /var/lib/pki/pki-tomcat
  sudo rm -rf /etc/pki/pki-tomcat
  sudo yum remove freeipa-* -y
fi

# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

pushd $DIST_DIR

sudo yum localinstall freeipa-* --enablerepo=updates-testing -y

popd

