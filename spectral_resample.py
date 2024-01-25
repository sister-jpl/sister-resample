#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTER
Space-based Imaging Spectroscopy and Thermal PathfindER
Author: Adam Chlus
"""

import datetime as dt
import glob
import json
import logging
import shutil
import sys
import os
import hytools as ht
from hytools.io.envi import WriteENVI
import numpy as np
from scipy.interpolate import interp1d
from skimage.util import view_as_blocks
from PIL import Image
import pystac
import spectral.io.envi as envi

def main():
    ''' Perform a two-step spectral resampling to 10nm. First wavelengths are aggregated
    to approximateley 10nm, then aggregated spectra a interpolated to exactly 10nm using a
    piecewise interpolator.
    '''

    # Set up console logging using root logger
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
    logger = logging.getLogger("sister-resample")
    # Set up file handler logging
    handler = logging.FileHandler("pge_run.log")
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(module)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("Starting spectral_resample.py")

    run_config_json = sys.argv[1]

    with open(run_config_json, 'r') as in_file:
        run_config =json.load(in_file)

    experimental = run_config['inputs']['experimental']
    if experimental:
        disclaimer = "(DISCLAIMER: THIS DATA IS EXPERIMENTAL AND NOT INTENDED FOR SCIENTIFIC USE) "
    else:
        disclaimer = ""

    os.mkdir('output')

    print ("Resampling reflectance")

    rfl_base_name = os.path.basename(run_config['inputs']['reflectance_dataset'])
    sister,sensor,level,product,datetime,in_crid = rfl_base_name.split('_')

    crid = run_config['inputs']['crid']

    rfl_file = f"{run_config['inputs']['reflectance_dataset']}/{rfl_base_name}.bin"

    out_rfl_file =  f'output/SISTER_{sensor}_L2A_RSRFL_{datetime}_{crid}.bin'

    resample(rfl_file,out_rfl_file,disclaimer, logger)

    generate_quicklook(out_rfl_file)

    print ("Resampling uncertainty")

    unc_base_name = os.path.basename(run_config['inputs']['uncertainty_dataset'])
    sister,sensor,level,product,datetime,in_crid,subproduct = unc_base_name.split('_')

    unc_file = f"{run_config['inputs']['uncertainty_dataset']}/{unc_base_name}.bin"

    out_unc_file = f'output/SISTER_{sensor}_L2A_RSRFL_{datetime}_{crid}_UNC.bin'

    resample(unc_file,out_unc_file,disclaimer, logger)

    # If experimental, prefix filenames with "EXPERIMENTAL-"
    if experimental:
        for file in glob.glob(f"output/SISTER*"):
            shutil.move(file, f"output/EXPERIMENTAL-{os.path.basename(file)}")

    rsrfl_file = glob.glob("output/*%s.bin" % run_config['inputs']['crid'])[0]
    rsrfl_basename = os.path.basename(rsrfl_file)[:-4]

    output_runconfig_path = f'output/{rsrfl_basename}.runconfig.json'
    shutil.copyfile(run_config_json, output_runconfig_path)

    output_log_path = f'output/{rsrfl_basename}.log'
    if os.path.exists("pge_run.log"):
        shutil.copyfile('pge_run.log', output_log_path)

    # Generate STAC
    catalog = pystac.Catalog(id=rsrfl_basename,
                             description=f'{disclaimer}This catalog contains the output data products of the SISTER '
                                         f'resampled reflectance PGE, including resampled reflectance and resampled '
                                         f'reflectance uncertainty. Execution artifacts including the runconfig file '
                                         f'and execution log file are included with the resampled reflectance data.')

    # Add items for data products
    hdr_files = glob.glob("output/*SISTER*.hdr")
    hdr_files.sort()
    for hdr_file in hdr_files:
        # TODO: Use incoming item.json to get properties and geometry and use hdr_file for description (?)
        metadata = generate_stac_metadata(hdr_file)
        assets = {
            "envi_binary": f"./{os.path.basename(hdr_file.replace('.hdr', '.bin'))}",
            "envi_header": f"./{os.path.basename(hdr_file)}"
        }
        # If it's the reflectance product, then add png, runconfig, and log
        if os.path.basename(hdr_file) == f"{rsrfl_basename}.hdr":
            png_file = hdr_file.replace(".hdr", ".png")
            assets["browse"] = f"./{os.path.basename(png_file)}"
            assets["runconfig"] = f"./{os.path.basename(output_runconfig_path)}"
            if os.path.exists(output_log_path):
                assets["log"] = f"./{os.path.basename(output_log_path)}"
        item = create_item(metadata, assets)
        catalog.add_item(item)

    # set catalog hrefs
    catalog.normalize_hrefs(f"./output/{rsrfl_basename}")

    # save the catalog
    catalog.describe()
    catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
    print("Catalog HREF: ", catalog.get_self_href())
    # print("Item HREF: ", item.get_self_href())

    # Move the assets from the output directory to the stac item directories and create empty .met.json
    for item in catalog.get_items():
        for asset in item.assets.values():
            fname = os.path.basename(asset.href)
            shutil.move(f"output/{fname}", f"output/{rsrfl_basename}/{item.id}/{fname}")
        with open(f"output/{rsrfl_basename}/{item.id}/{item.id}.met.json", mode="w"):
            pass


def gaussian(x,mu,fwhm):

    c = fwhm/(2* np.sqrt(2*np.log(2)))
    return np.exp(-1*((x-mu)**2/(2*c**2)))


def resample(in_file,out_file,disclaimer, logger):

    image = ht.HyTools()
    image.read_file(in_file,'envi')

    if image.wavelengths.max()< 1100:
        new_waves = np.arange(400,991,10)
    else:
        new_waves = np.arange(400,2501,10)

    bins = int(np.round(10/np.diff(image.wavelengths).mean()))
    agg_waves  = np.nanmean(view_as_blocks(image.wavelengths[:(image.bands//bins) * bins],
                                           (bins,)),axis=1)

    if bins ==1 :
        agg_fwhm  = image.fwhm

    else:
        hi_res_waves = np.arange(350,2600)
        fwhm_array = np.zeros((image.bands,2600-350))

        for i,(wave,fwhm) in enumerate(zip(image.wavelengths,image.fwhm)):
            fwhm_array[i] = gaussian(hi_res_waves,wave,fwhm)

        sum_fwhm  = np.nansum(view_as_blocks(fwhm_array[:(image.bands//bins) * bins],
                                               (bins,2600-350)),axis=(1,2))
        agg_fwhm = []
        for i in range(len(agg_waves)):
            arg_max = np.argmax(sum_fwhm[i])
            half_max =  sum_fwhm[i].max()/2
            diff = np.abs(sum_fwhm[i]-half_max)
            end = arg_max + np.argmin(diff[arg_max:])
            start = np.argmin(diff[:arg_max])
            agg_fwhm.append(hi_res_waves[end] - hi_res_waves[start])

    #True resampled FWHM is difficult to determine, using a simple nearest neighbor approximation
    resampled_fwhm = interp1d(agg_waves,agg_fwhm,fill_value = 'extrapolate', kind = 'nearest')(new_waves)

    logger.info(f"Aggregating every {bins} bands")

    out_header = image.get_header()
    out_header['bands'] = len(new_waves)
    out_header['wavelength'] = new_waves.tolist()
    out_header['fwhm'] = resampled_fwhm
    out_header['default bands'] = []

    if  "UNC" in in_file:
        out_header['description'] =f'{disclaimer}10 nm resampled reflectance uncertainty'
    else:
        out_header['description'] =f'{disclaimer}10 nm resampled reflectance'

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


def generate_stac_metadata(header_file):

    header = envi.read_envi_header(header_file)
    base_name = os.path.basename(header_file)[:-4]

    metadata = {}
    metadata['id'] = base_name
    metadata['start_datetime'] = dt.datetime.strptime(header['start acquisition time'], "%Y-%m-%dt%H:%M:%Sz")
    metadata['end_datetime'] = dt.datetime.strptime(header['end acquisition time'], "%Y-%m-%dt%H:%M:%Sz")
    # Split corner coordinates string into list
    coords = [float(x) for x in header['bounding box'].replace(']', '').replace('[', '').split(',')]
    geometry = [list(x) for x in zip(coords[::2], coords[1::2])]
    # Add first coord to the end of the list to close the polygon
    geometry.append(geometry[0])
    metadata['geometry'] = {
        "type": "Polygon",
        "coordinates": geometry
    }
    base_tokens = base_name.split('_')
    metadata['collection'] = f"SISTER_{base_tokens[1]}_{base_tokens[2]}_{base_tokens[3]}_{base_tokens[5]}"
    product = base_tokens[3]
    if "UNC" in base_name:
        product += "_UNC"
    metadata['properties'] = {
        'sensor': base_tokens[1],
        'description': header['description'],
        'product': product,
        'processing_level': base_tokens[2]
    }
    return metadata


def create_item(metadata, assets):
    item = pystac.Item(
        id=metadata['id'],
        datetime=metadata['start_datetime'],
        start_datetime=metadata['start_datetime'],
        end_datetime=metadata['end_datetime'],
        geometry=metadata['geometry'],
        collection=metadata['collection'],
        bbox=None,
        properties=metadata['properties']
    )
    # Add assets
    for key, href in assets.items():
        item.add_asset(key=key, asset=pystac.Asset(href=href))
    return item


if __name__ == "__main__":
    main()
