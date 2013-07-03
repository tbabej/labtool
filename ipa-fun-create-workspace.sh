# Load the configuration
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

function recreate_dir(){
# mkdir -p creates directory only if it does not exist
  rm -rf $1
  sudo mkdir -p $1
  sudo chown -R $USER $1
}

if [[ $1 == 'original' ]]
then
  GIT_PATH=git://git.fedorahosted.org/git/freeipa.git
elif [[ $1 == 'backup' ]]
then
  GIT_PATH=https://github.com/encukou/freeipa.git
else
  echo "Usage: $0 original|backup"
  exit 1
fi

# Create working dir directory structure
recreate_dir $WORKING_DIR
recreate_dir $DIST_DIR
recreate_dir $PATCH_DIR
recreate_dir $LOG_DIR

pushd $WORKING_DIR

# Remove any remnants of previous repositories
rm -rf freeipa

# Clone FreeIPA so we have our own sandbox to play in
git clone -q $GIT_PATH

popd


