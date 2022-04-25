set -E

imgspec_dir=$(cd "$(dirname "$0")" ; pwd -P)
pge_dir=$(dirname ${imgspec_dir})

mkdir output
tar_file=$(ls input/*tar.gz)
base=$(basename $tar_file)
scene_id=${base%.tar.gz}

if  [[ $scene_id == "ang"* ]]; then
    out_dir=$(echo $scene_id | cut -c1-18)_chla
elif [[ $scene_id == "PRS"* ]]; then
    out_dir=$(echo $scene_id | cut -c1-38)_chla
elif [[ $scene_id == "f"* ]]; then
    out_dir=$(echo $scene_id | cut -c1-16)_chla
fi

mkdir output/$out_dir

source activate base
conda install -yc conda-forge numpy scipy scikit-image
pip install --user hy-tools-lite

tar -xzvf $tar_file -C input

for a in `python ${imgspec_dir}/get_paths_from_granules.py`;
   do
      if [[($a == *"loc"*) || ($a == *"ort_igm"*)]]; then
         echo 'Orthocorrecting loc file'
         loc_file=`python ${imgspec_dir}/create_loc_ort.py $a`
         python ${pge_dir}/spatial_resample.py $loc_file output/$out_dir --verbose;
      elif [[($a == *"rfl"*) || ($a == *"corr"*)]]; then
         python ${pge_dir}/spectral_resample.py $a output/$out_dir;
      else
         python ${pge_dir}/spatial_resample.py $a output/$out_dir --verbose;
      fi
  done

cd output
tar -czvf $out_dir.tar.gz $out_dir
rm -r $out_dir
