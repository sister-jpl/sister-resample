# sister-resample
This repository contains scripts to resample imagery to SGB-like spectral and spatial
resolutions.

## Installation

```bash
pip -r requirements.txt
```

## Use

### Spatial resampler

```bash
python spatial_resmaple.py input_image output_directory
```

Optional arguments:

- `--pixel`: Pixel size, in map units, default = 30
- `--verbose`: default = False

### Spectral resampler

```bash
python spectral_resample.py input_image output_directory
```

Optional arguments:

- `--type`: Interpolator type [(options)](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp1d.html), default = linear
- `--verbose`: default = False
