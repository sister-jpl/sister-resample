#!/bin/bash

set -E

source activate sister

imgspec_dir=$(cd "$(dirname "$0")" ; pwd -P)
pge_dir=$(dirname ${imgspec_dir})

mkdir output

tar -xzvf input/*.tar.gz -C input

rfl_path=$(ls input/*/*RFL* | grep -v '.hdr')
unc_path=$(ls input/*/*UNC* | grep -v '.hdr')

# Create output directory
rfl_name=$(basename $rfl_path)
output_base_name=$(echo "${rdn_name/L2A_RFL/"L2A_RSRFL"}")
mkdir output/$output_base_name

# Resample uncertainty and reflectance
python ${pge_dir}/spectral_resample.py $rfl_path output/$output_base_name
python ${pge_dir}/spectral_resample.py $unc_path output/$output_base_name


#Rename, compress and cleanup outputs

cd output
tar -czvf ${output_base_name}.tar.gz $output_base_name
rm -r $output_base_name
