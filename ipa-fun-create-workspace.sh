# Load the configuration
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

if [[ $1 == 'original' ]]
then
  GIT_PATH=git://git.fedorahosted.org/git/freeipa.git
elif [[ $1 == 'backup' ]]
then
  GIT_PATH=https://github.com/encukou/freeipa.git
else
  echo "Usage: $0 original|backup destination"
  exit 1
fi

# Check if destination was given as option
if [[ ! $2 == "" ]]
then
  if [[ -d $WORKING_DIR/$2 ]]
  then
    echo "$WORKING_DIR/$2 does exist, removing content."
    sudo rm -rf $WORKING_DIR/$2
  fi

  echo "$WORKING_DIR/$2 does not exist, creating."
  mkdir $WORKING_DIR/$2
else
  echo 'No destination given'
  exit 1
fi

sudo mkdir $ROOT_BUILD
sudo chown $USER $ROOT_BUILD
pushd $ROOT_BUILD

# Remove any remnants of previous repositories
rm -rf freeipa

# Clone FreeIPA so we have our own sandbox to play in
if [[ `ls | wc -l` == 0 ]]
then
  git clone -q $GIT_PATH
fi

popd


