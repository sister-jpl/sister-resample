imgspec_dir=$(cd "$(dirname "$0")" ; pwd -P)
pge_dir=$(dirname ${imgspec_dir})

mkdir output
tar_file=$(ls input/*tar.gz)

base=$(basename $tar_file)
output_dir=output/${base%.tar.gz}

tar -xzvf $tar_file -C input

for a in `python get_paths_from_granules.py`; 
   do 
      if [[ $a == *"loc"* ]]; then
         echo 'Orthocorrecting loc file'
         python ${imgspec_dir}/create_loc_ort.py $a
         python ${pge_dir}/spatial_resample.py "${a}_ort" $output_dir --verbose;
      elif [[ $a == *"rfl"* ]]; then
         python ${pge_dir}/spectral_resample.py $a $output_dir --verbose;
      else
         python ${pge_dir}/spatial_resample.py $a $output_dir --verbose;
      fi
  done

tar -czvf $output_dir.tar.gz $output_dir
rm -r $output_dir
