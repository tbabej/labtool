#! /bin/bash

##############################################################################
# Author: Tomas Babej <tbabej@redhat.com>
#
# Makes sure that all the IPA-related services are up and running.
#
# Usage: $0
# Returns: 0 on success, 1 on failure
##############################################################################


# If any command here fails, exit the script
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh


# Get the list of services
TEXT=`sudo ipactl status 2>/dev/null | grep Service: `

# Start each service that is not started, recursively, untill all are
while [[ `echo "$TEXT" | grep STOPPED` != '' ]]
do
  SERVICE=`echo "$TEXT" | grep STOPPED | head -n 1 | cut -d ' ' -f1`

  # Start dirsrv.target instead of the correct instance
  # TODO: detect the instance name and start the instance only
  if [[ $SERVICE == "Directory" ]]
  then
    sudo systemctl start dirsrv.target 2>/dev/null 1>/dev/null
  fi

  echo "Service $SERVICE not running, starting"
  sudo service $SERVICE start 2>/dev/null 1>/dev/null
  TEXT=`sudo ipactl status 2>/dev/null | grep Service:`
done

echo "All services are up and running."
