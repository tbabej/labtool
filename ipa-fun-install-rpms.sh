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

# Set DIST_DIR if given via command line
if [[ ! $1 == "" ]]
then
  if [[ ! -d $WORKING_DIR/$1 ]]
  then
    echo "$WORKING_DIR/$1 does not exist"
    exit 1
  fi

  DIST_DIR=$WORKING_DIR/$1/dist
fi

pushd $DIST_DIR

sudo yum localinstall freeipa-* -y

popd

