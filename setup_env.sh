#!/usr/bin/env bash

# installing required linux packages and venv
grep 'debian' '/etc/os-release' > /dev/null
if [ $? -ne 0 ]; then
  sudo yum install -y python3-venv python3-devel gcc
  sudo yum groupinstall 'Development Tools'
else
  sudo apt-get update && sudo apt-get upgrade
  sudo apt-get install -y python3.10-venv build-essential python3.10-dev gcc
fi

# create and activate venv
in_venv=$(python3 -c 'import sys; return sys.prefix != sys.base_prefix')
if ! ${in_venv}; then
  python3 -m venv venv
  source venv/bin/activate
fi
python3 -m pip install -r requirements.txt

# build python module
cd thirdparty
CC=gcc python3 setup.py install --quiet
