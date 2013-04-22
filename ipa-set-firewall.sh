#! /bin/bash

# Configures the firewall

# Use default in config.sh if no option was given.
if [[ $1 == "" ]]
then
  DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
  source $DIR/config.sh
elif [[ $1 == "on" ]]
then
  FIREWALL_ENABLED=1
elif [[ $1 == "off" ]]
then
  FIREWALL_ENABLED=0
else
  echo "Usage: $0 [on|off]"
  exit 1
fi


if [[ $FIREWALL_ENABLED == 0 ]]
then
  echo "Disabling firewall."
  sudo systemctl stop firewalld.service
  sudo systemctl disable firewalld.service
  sudo service iptables stop
  sudo service iptables6 stop
  sudo chkconfig iptables off
  sudo chkconfig iptables6 off
  sudo iptables -F
else
  echo "Enabling firewall."
  sudo systemctl enable firewalld.service
  sudo systemctl start firewalld.service
fi

exit 0
