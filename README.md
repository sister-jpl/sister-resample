# SISTER Spectral Resample PGE Documentation

## Description

The L2A spectral resample PGE takes as input surface reflectance and uncertainty images and spectrally resamples the data
to 10nm spectral spacing. Spectral resampling is performed in a two-step process, first bands are aggregated and averaged to the closest resolution to the target resolution (10 nm). For example DESIS data, which has an average spectral spacing of 2.55 nm, is aggregated and averaged every 4 bands. Next a piecewise cubic interpolator is used to interpolate the spectra to the target wavelength spacing. Output range for all sensors except DESIS is 400-2500 nm, while the DESIS output range is 400-990 nm.

![DESIS spectral resampling example](./figures/spectral_resample_example.png)

## PGE Arguments

In addition to required MAAP job submission arguments the L2A spectral resampling PGE also takes the following argument(s):


|Argument| Type |  Description | Default|
|---|---|---|---|
| l2a_granule| string |L2A ISOFIT dataset granule URL| -|


## Outputs

The L2A spectral resampling PGE exports 2 ENVI formatted datacubes along with their associated header files. The outputs of the PGE use the following naming convention:

    SISTER_<SENSOR>_L2A_RSRFL_<YYYYMMDDTHHMMSS>_CRID<_SUBPRODUCT>
    
Additionally, a false color quicklook PNG image is produced of the radiance image using wavelengths 560, 850 and 660 nm for DESIS and 560, 850, 1600 nm for all other sensors.

|Product name| Description |  Units | Example filename |
|---|---|---|---|
| \*RSRFL\*.bin| ENVI 10nm reflectance datacube | % | SISTER\_AVNG\_L2A\_RSRFL\_20220502T180901\_001.bin|
|  \*RSRFL\*.hdr| ENVI 10nm reflectance header file  | - | SISTER\_AVNG\_L2A\_RSRFL\_20220502T180901\_001.hdr|
|  \*RSUNC\*.bin| ENVI 10nm uncertainty datacube | % | SISTER\_AVNG\_L2A\_RSRFL\_20220502T180901\_001_RSUNC.bin|
|  \*RSUNC\*.hdr| ENVI 10nm uncertainty header file  | - |SISTER\_AVNG\_L2A\_RSRFL\_20220502T180901\_001_RSUNC.hdr|
| *.png| 10nm reflectance quicklook | % | SISTER\_AVNG\_L2A\_RSRFL_20220502T180901\_001.png|


## Algorithm registration

	from maap.maap import MAAP
	maap = MAAP(maap_host="sister-api.imgspec.org")
	
	resample_alg = {
	    "script_command": "sister-resample/pge_run.sh",
	    "repo_url": "https://github.com/EnSpec/sister-resample.git",
	    "algorithm_name":"2.0.0",
	    "code_version":"sister-dev",
	    "algorithm_description":"Spectrally resample reflectance and uncertainty images",
	    "environment_name":"ubuntu",
	    "disk_space":"50GB",
	    "queue": "sister-job_worker-16gb",
	    "build_command": "sister-resample/install.sh",
	    "docker_container_url": docker_container_url,
	    "algorithm_params":[
	        {
	            "field": "l2a_granule",
	            "type": "file"
	        },
	          {
	            "field": "CRID",
	            "type": "config",
	            "default": "000"
	        }
	    ]
	}
	
	response = maap.registerAlgorithm(resample_alg)

## Example

	resample_job_response = maap.submitJob(
	    algo_id="sister-resample",
	    version="2.0.0",
	    l2a_granule= '../AVNG_20220502T180901_L2A_RFL_001.tar.gz',
	    CRID = '001'
	    publish_to_cmr=False,
	    cmr_metadata={},
	    queue="sister-job_worker-16gb",
	    identifier='SISTER_AVNG_20170827T175432_L2A_RSRFL_001"
