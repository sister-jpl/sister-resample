# SISTER Spectral Resample PGE Documentation

## Description

The L2A spectral resample PGE takes as input surface reflectance and uncertainty images and spectrally resamples the data
to 10nm spectral spacing. Spectral resampling is performed in a two-step process, first bands are aggregated and averaged 
to the closest resolution to the target resolution (10 nm). For example DESIS data, which has an average spectral spacing 
of 2.55 nm, is aggregated and averaged every 4 bands. Next a piecewise cubic interpolator is used to interpolate the spectra 
to the target wavelength spacing. Output range for all sensors except DESIS is 400-2500 nm, while the DESIS output range 
is 400-990 nm.

![DESIS spectral resampling example](./figures/spectral_resample_example.png)

## PGE Arguments

The L2A spectral resampling PGE takes the following argument(s):


| Argument            | Description                          | Default |
|---------------------|--------------------------------------|---------|
| reflectance_dataset | L2A reflectance dataset              | -       |
| uncertainty_dataset | L2A uncertainty dataset              | -       |
| crid                | Composite release identifier         | '000'   |
| experimental        | Designates outputs as "experimental" | 'True'  |

## Outputs

The outputs of the L2A spectral resampling PGE use the following naming convention:

    (EXPERIMENTAL-)SISTER_<SENSOR>_L2A_RSRFL_<YYYYMMDDTHHMMSS>_<CRID>_<SUBPRODUCT>
    
Note that the "EXPERIMENTAL-" prefix is optional and is only added when the "experimental" flag is set to True.

The following data products are produced:

| Product description                             | Units | Example filename                                              |
|-------------------------------------------------|-------|---------------------------------------------------------------|
| ENVI 10nm Resampled reflectance datacube        | %     | SISTER\_AVCL\_L2A\_RSRFL\_20110513T175417\_000.bin            |
| ENVI 10nm Resampled reflectance header file     | -     | SISTER\_AVCL\_L2A\_RSRFL\_20110513T175417\_000.hdr            |
| Resampled reflectance metadata (STAC formatted) | -     | SISTER\_AVCL\_L2A\_RSRFL\_20110513T175417\_000.json           |
| False color reflectance quicklook               | -     | SISTER\_AVCL\_L2A\_RSRFL\_20110513T175417\_000.png            |
| ENVI 10nm Resampled uncertainty datacube        | %     | SISTER\_AVCL\_L2A\_RSRFL\_20110513T175417\_000_UNC.bin        |
| ENVI 10nm Resampled uncertainty header file     | -     | SISTER\_AVCL\_L2A\_RSRFL\_20110513T175417\_000_UNC.hdr        |
| Resampled uncertainty metedata (STAC formatted) | -     | SISTER\_AVCL\_L2A\_RSRFL\_20110513T175417\_000_UNC.json       |
| PGE runconfig                                   | -     | SISTER\_AVCL\_L2A\_RSRFL\_20110513T175417\_000.runconfig.json |
| PGE log                                         | -     | SISTER\_AVCL\_L2A\_RSRFL\_20110513T175417\_000.log            |

Metadata files are [STAC formatted](https://stacspec.org/en) and compatible with tools in the [STAC ecosystem](https://stacindex.org/ecosystem).

## Executing the Algorithm

This algorithm requires [Anaconda Python](https://www.anaconda.com/download)

To install and run the code, first clone the repository and execute the install script:

    git clone https://github.com/sister-jpl/sister-resample.git
    cd sister-resample
    ./install.sh
    cd ..

Then, create a working directory and enter it:

    mkdir WORK_DIR
    cd WORK_DIR

Copy input files to the work directory. For each "dataset" input, create a folder with the dataset name, then download 
the data file(s) and STAC JSON file into the folder.  For example, the reflectance dataset input would look like this:

    WORK_DIR/SISTER_AVCL_L2A_RFL_20110513T175417_000/SISTER_AVCL_L2A_RFL_20110513T175417_000.bin
    WORK_DIR/SISTER_AVCL_L2A_RFL_20110513T175417_000/SISTER_AVCL_L2A_RFL_20110513T175417_000.hdr
    WORK_DIR/SISTER_AVCL_L2A_RFL_20110513T175417_000/SISTER_AVCL_L2A_RFL_20110513T175417_000.json

Finally, run the code 

    ../sister-resample/pge_run.sh --reflectance_dataset SISTER_AVCL_L2A_RFL_20110513T175417_000 --uncertainty_dataset SISTER_AVCL_L2A_RFL_20110513T175417_000_UNC

