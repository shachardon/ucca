#!/usr/bin/env bash

export CXX="g++-4.8" CC="gcc-4.8"
cd $HOME
git clone https://github.com/clab/dynet
cd dynet
hg clone https://bitbucket.org/eigen/eigen
wget https://raw.githubusercontent.com/danielhers/bilstm-aux/master/dynet_py3_patch.diff
git apply dynet_py3_patch.diff
mkdir build
cd build
cmake .. -DEIGEN3_INCLUDE_DIR=eigen -DPYTHON=`which python`
make
cd python
python setup.py install