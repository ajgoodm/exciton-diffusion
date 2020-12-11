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


virtual_env=$(pyenv versions | grep "$VIRTUAL_PY")
case "$virtual_env" in
  *$VIRTUAL_PY*) 
  echo "Python virtual env '$VIRTUAL_PY' is already created"
  ;;   # the PYTHON_VER is already installed - nothing to do
  *)
    echo "Python virtual env '$VIRTUAL_PY' is not created - creating now..."
    pyenv virtualenv $PYTHON_VER $VIRTUAL_PY

    [ $? -ne 0 ] && echo "ERROR: Unable to create python virtual env" && exit 1
  ;;
esac

echo "Setting local python virtual env"

pyenv local $VIRTUAL_PY

echo "INSTALL DEPENDENCIES"

pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e . \
    || echo "ERROR: Failed to install the package, is this script running from the folder with setup.py?" \
    && exit 1
