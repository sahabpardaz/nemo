# A script to get the current version of Nemo.
# Execute this script to print the version.

readonly CWD="$( dirname "$( readlink -f "$0" )" )"

# Only read NEMO_VERSION from .env file.
eval $(. "$CWD/.env"; echo NEMO_VERSION="$NEMO_VERSION")

echo "$NEMO_VERSION"
