#!/bin/bash

pge_dir=$(cd "$(dirname "$0")" ; pwd -P)

# Need to do custom install to prevent dependency errors
conda create -y --name sister python=3.8
source activate sister

git clone https://github.com/EnSpec/hytools.git -b 1.5.0
cd hytools
pip install .

pip install scikit-image==0.19.3
