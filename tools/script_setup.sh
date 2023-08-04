#!/bin/bash
[ ! -z $DEBUG ] && set -x

CWD=$(pwd)
cd $(dirname $0)/..
REPO_ROOT=$(pwd)
cd $CWD

TOOLS_DIR=$REPO_ROOT/tools
PYTHON_VER=3.10.11
