set -E

imgspec_dir=$(cd "$(dirname "$0")" ; pwd -P)
pge_dir=$(dirname ${imgspec_dir})

mkdir output
tar_file=$(ls input/*tar.gz)
base=$(basename $tar_file)
output_dir=${base%.tar.gz}
mkdir output/$output_dir

source activate base
conda install -c conda-forge numpy scipy scikit-image
pip install --user hy-tools-lite

tar -xzvf $tar_file -C input

for a in `python ${imgspec_dir}/get_paths_from_granules.py`;
   do
      if [[($a == *"loc"*) || ($a == *"ort_igm"*)]]; then
         echo 'Orthocorrecting loc file'
         loc_file=`python ${imgspec_dir}/create_loc_ort.py $a`
         python ${pge_dir}/spatial_resample.py $loc_file output/$output_dir --verbose;
      elif [[($a == *"rfl"*) || ($a == *"corr"*)]]; then
         python ${pge_dir}/spectral_resample.py $a output/$output_dir;
      else
         python ${pge_dir}/spatial_resample.py $a output/$output_dir --verbose;
      fi
  done

cd output
tar -czvf $output_dir.tar.gz $output_dir
rm -r $output_dir
