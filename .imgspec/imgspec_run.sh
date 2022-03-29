imgspec_dir=$(cd "$(dirname "$0")" ; pwd -P)
pge_dir=$(dirname ${imgspec_dir})
echo $pge_dir
mkdir output

string='location'

for a in `python get_paths_from_granules.py`; 
	do 
	  if [[ $a == *"loc"* ]]; then
	    echo 'Orthocorrecting loc file'
	    python ${imgspec_dir}/create_loc_ort.py $a
	    python ${pge_dir}/spatial_resample.py "${a}_ort" output --verbose;
	  else
	   python ${pge_dir}/spatial_resample.py $a output --verbose;
	  fi
	done

