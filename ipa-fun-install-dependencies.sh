#!/bin/bash

# Function - install dependencies
# TODO: add logging not some log file of all long outputs

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Sets correct repository for the platform used
case $PLATFORM in
  fc) REPO_NAME="ipa-devel-fedora.repo";;
  el) REPO_NAME="ipa-devel-rhel.repo" ;;
esac

if [[ $2 == 'devel' ]]
then
  # Configure devel repo
  if [ ! -f /etc/yum.repos.d/$REPO_NAME ]
  then
      if [ ! -f  ~/$REPO_NAME ]
      then
          pushd ~ >/dev/null
          wget http://jdennis.fedorapeople.org/ipa-devel/$REPO_NAME
      fi
      sudo cp ~/$REPO_NAME /etc/yum.repos.d/
      echo "Configuring $PLATFORM_NAME devel repo."
  else
      echo "$PLATFORM_NAME devel repo is already configured."
  fi
fi

# Install the dependencies
sudo yum install bind-dyndb-ldap selinux-policy-devel bash-completion -y --enablerepo=updates-testing

# We pass vm-xyz or local to the script if we want to install the dependencies
if [[ $1 == "build" ]]
then
  pushd $IPA_DIR
  sudo yum install rpm-build `grep "^BuildRequires" freeipa.spec.in | awk '{ print $2 }' | grep -v "^/"` -y --enablerepo=updates-testing
  popd
  #pushd $DIST_DIR
  #yum deplist * --disablerepo=updates-testing | grep provider | awk '{print $2}' | sort | uniq | grep -E "($ARCHITECTURE|noarch)" | sed ':a;N;$!ba;s/\n/ /g' | xargs sudo yum -y install
fi

# Update the system
sudo yum update -y --enablerepo=updates-testing
