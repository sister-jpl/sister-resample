set -E

imgspec_dir=$(cd "$(dirname "$0")" ; pwd -P)
pge_dir=$(dirname ${imgspec_dir})

mkdir output
tar_file=$(ls input/*tar.gz)
base=$(basename $tar_file)
scene_id=${base%.tar.gz}

if  [[ $scene_id == "ang"* ]]; then_rfl
    out_dir=$(echo $scene_id | cut -c1-18)
elif [[ $scene_id == "PRS"* ]]; then
    out_dir=$(echo $scene_id | cut -c1-38)_rfl
elif [[ $scene_id == "f"* ]]; then
    out_dir=$(echo $scene_id | cut -c1-16)_rfl
elif [[ $scene_id == "DESIS"* ]]; then
    out_dir=$(echo $scene_id | cut -c1-44)_rfl
fi

echo $out_dir

mkdir output/$out_dir

tar -xzvf $tar_file -C input

# Resample uncertainty and reflectacne
python ${pge_dir}/spectral_resample.py input/*/*rfl output/$out_dir;
python ${pge_dir}/spectral_resample.py input/*/*uncert output/$out_dir;

#cd output
#tar -czvf ${out_dir}.tar.gz $out_dir
#rm -r $out_dir
