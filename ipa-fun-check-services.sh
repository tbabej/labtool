#! /bin/bash

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

  # here we need to build worarkound for DS
  if [[ $SERVICE == "Directory" ]]
  then
    echo 'Directory service is not started, please restart.'
  fi

  echo "Service $SERVICE not running, starting"
  sudo service $SERVICE start 2>/dev/null 1>/dev/null
  TEXT=`sudo ipactl status 2>/dev/null | grep Service:`
done

echo "All services are up and running."
