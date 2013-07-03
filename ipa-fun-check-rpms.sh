# Checks whether rpms have already been built and are in expected location.

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

if [[ `ls $DIST_DIR | wc -l` -eq 0 ]]
then
  echo "There are no rpms in $DIST_DIR"
  exit 1
fi

