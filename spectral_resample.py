#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTER
Space-based Imaging Spectroscopy and Thermal PathfindER
Author: Adam Chlus
"""

import json
import sys
import os
import hytools as ht
from hytools.io.envi import WriteENVI
import numpy as np
from scipy.interpolate import interp1d
from skimage.util import view_as_blocks
from PIL import Image

def main():
    ''' Perform a two-step spectral resampling to 10nm. First wavelengths are aggregated
    to approximateley 10nm, then aggregated spectra a interpolated to exactly 10nm using a
    piecewise interpolator.
    '''

    run_config_json = sys.argv[1]

    with open(run_config_json, 'r') as in_file:
        run_config =json.load(in_file)

    os.mkdir('output')

    base_name = os.path.basename(run_config['inputs']['l2a_granule'])

    print ("Resampling reflectance")
    rfl_file = f'input/{base_name}/{base_name}.bin'
    rfl_out_file =  f'output/{base_name.replace("RFL","RSRFL")}.bin'
    rfl_met = f'input/{base_name}/{base_name}.met.json'
    rfl_out_met = rfl_out_file.replace('.bin','.met.json')

    resample(rfl_file,rfl_out_file)

    generate_metadata(rfl_met,rfl_out_met,
                      {'product': 'RSRFL',
                      'processing_level': 'L2A',
                      'description' : '10nm resampled reflectance'})

    generate_quicklook(rfl_out_file)


    print ("Resampling uncertainty")
    unc_file = f'input/{base_name}/{base_name}_UNC.bin'
    unc_out_file = rfl_out_file.replace('.bin','_RSUNC.bin')
    unc_met = f'input/{base_name}/{base_name}_UNC.met.json'
    unc_out_met = unc_out_file.replace('.bin','.met.json')

    resample(unc_file,unc_out_file)

    generate_metadata(unc_met,unc_out_met,
                      {'product': 'RSUNC',
                      'processing_level': 'L2A',
                      'description' : '10nm resampled uncertainty'})


def generate_metadata(in_file,out_file,metadata):

    with open(in_file, 'r') as in_obj:
        in_met =json.load(in_obj)

    for key,value in metadata.items():
        in_met[key] = value

    with open(out_file, 'w') as out_obj:
        json.dump(in_met,out_obj,indent=3)

def resample(in_file,out_file):

    image = ht.HyTools()
    image.read_file(in_file,'envi')

    if image.wavelengths.max()< 1100:
        new_waves = np.arange(400,991,10)
    else:
        new_waves = np.arange(400,2501,10)

    bins = int(np.round(10/np.diff(image.wavelengths).mean()))
    agg_waves  = np.nanmean(view_as_blocks(image.wavelengths[:(image.bands//bins) * bins],
                                           (bins,)),axis=1)
    agg_fwhm  = np.nanmean(view_as_blocks(image.fwhm[:(image.bands//bins) * bins],
                                           (bins,)),axis=1)

    print(f"Aggregating every {bins} bands")

    out_header = image.get_header()
    out_header['bands'] = len(new_waves)
    out_header['wavelength'] = new_waves.tolist()
    out_header['fwhm'] = agg_fwhm
    out_header['default bands'] = []

    writer = WriteENVI(out_file,out_header)
    iterator =image.iterate(by = 'line')

    while not iterator.complete:
        line = iterator.read_next()[:,:(image.bands//bins) * bins]
        line  = np.nanmean(view_as_blocks(line,(1,bins,)),axis=(2,3))
        interpolator = interp1d(agg_waves,line,fill_value = 'extrapolate', kind = 'cubic')
        line = interpolator(new_waves)
        writer.write_line(line,iterator.current_line)


def generate_quicklook(input_file):

    img = ht.HyTools()
    img.read_file(input_file)
    image_file = input_file.replace('.bin','.png')

    if 'DESIS' in img.base_name:
        band3 = img.get_wave(560)
        band2 = img.get_wave(850)
        band1 = img.get_wave(660)
    else:
        band3 = img.get_wave(560)
        band2 = img.get_wave(850)
        band1 = img.get_wave(1660)

    rgb=  np.stack([band1,band2,band3])
    rgb[rgb == img.no_data] = np.nan

    rgb = np.moveaxis(rgb,0,-1).astype(float)
    bottom = np.nanpercentile(rgb,5,axis = (0,1))
    top = np.nanpercentile(rgb,95,axis = (0,1))
    rgb = np.clip(rgb,bottom,top)
    rgb = (rgb-np.nanmin(rgb,axis=(0,1)))/(np.nanmax(rgb,axis= (0,1))-np.nanmin(rgb,axis= (0,1)))
    rgb = (rgb*255).astype(np.uint8)

    im = Image.fromarray(rgb)
    im.save(image_file)

if __name__ == "__main__":
    main()
