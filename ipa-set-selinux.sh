#! /bin/bash

# Disables / enables SELinux permanently

# Use default in config.sh if no option was given.
if [[ $1 == "" ]]
then
  DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
  source $DIR/config.sh
elif [[ $1 == "on" ]]
then
  SELINUX_ENFORCING=1
elif [[ $1 == "off" ]]
then
  SELINUX_ENFORCING=0
else
  echo "Usage: $0 [on|off]"
  exit 1
fi

if [[ $SELINUX_ENFORCING == 0 ]]
then
  echo 'Disabling SELinux'
  sudo setenforce 0
  sudo sed -i 's/^SELINUX=.*/SELINUX=permissive/' /etc/selinux/config
else
  echo 'Enabling SELinux'
  sudo setenforce 1
  sudo sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config
fi

exit 0
