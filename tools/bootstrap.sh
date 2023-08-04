#!/bin/bash
. $(dirname $0)/script_setup.sh

echo "BOOTSTRAPPING PYTHON ENVIRONMENT"

installed_version=$(pyenv versions | grep "$PYTHON_VER")

case "$installed_version" in
*$PYTHON_VER*)
	echo "Python version '$PYTHON_VER' is already installed"
	;;
*)
	echo "Python version '$PYTHON_VER' is not installed - installing now..."
	pyenv install $PYTHON_VER

	# [ $? -ne 0 ] && echo "ERROR: Unable to install required python version" && exit 1
	;;
esac

poetry install
