# Checks whether rpms have already been built and are in expected location.

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

if [[ `ls $DIST_DIR | wc -l` -eq 0 ]]
then
  echo "There are no rpms in $DIST_DIR"
  exit 1
fi

