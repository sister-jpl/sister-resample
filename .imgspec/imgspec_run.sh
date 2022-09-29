#!/bin/bash

set -E

source activate sister

imgspec_dir=$(cd "$(dirname "$0")" ; pwd -P)
pge_dir=$(dirname ${imgspec_dir})

mkdir output

tar -xzvf input/*.tar.gz -C input

rfl_path=$(ls input/*/*RFL* | grep -v '.hdr\|.log')
unc_path=$(ls input/*/*UNC* | grep -v '.hdr')

echo "Found input RFL file: $rfl_path"
echo "Found input UNC file: $unc_path"

# Create output directory
rfl_name=$(basename $rfl_path)
output_base_name=$(echo "${rfl_name/L2A_RFL/"L2A_RSRFL"}")
mkdir output/$output_base_name

# Resample uncertainty and reflectance
python ${pge_dir}/spectral_resample.py $rfl_path output/$output_base_name
python ${pge_dir}/spectral_resample.py $unc_path output/$output_base_name

#Rename, compress and cleanup outputs
cd output

mv */*_RFL*.hdr $output_base_name/$output_base_name.hdr
mv */*_RFL* $output_base_name/$output_base_name

mv */*_UNC*.hdr $output_base_name/$(echo "${output_base_name/RSRFL/"RSUNC"}").hdr
mv */*_UNC* $output_base_name/$(echo "${output_base_name/RSRFL/"RSUNC"}")

#Create metadata
python ${imgspec_dir}/generate_metadata.py */*RSRFL*.hdr .

# Create quicklook
python ${imgspec_dir}/generate_quicklook.py $(ls */*RSRFL* | grep -v '.hdr') .


tar -czvf ${output_base_name}.tar.gz $output_base_name
rm -r $output_base_name
