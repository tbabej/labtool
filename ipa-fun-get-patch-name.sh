# Get the patch name from the number

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $DIR/config.sh

# Validate patch name
if [[ $1 == "" ]]
then
  echo "Usage: $0 patch_number"
  exit 1
else
  MATCHES=`find $PATCH_DIR -name \*$1\* | wc -l`
  if [[ ! $MATCHES == 1 ]]
  then
    echo "There is unappropriate number($MATCHES) of patches matching $1 in $PATCH_DIR"
    exit 2
  else
    PATCH=`find $PATCH_DIR -name \*$1\*`
  fi
fi

echo $PATCH
