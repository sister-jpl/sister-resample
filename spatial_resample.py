#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTER
Space-based Imaging Spectroscopy and Thermal PathfindER
Author: Adam Chlus
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
import os
import hytools_lite as htl
from hytools_lite.io.envi import WriteENVI
import numpy as np
from skimage.util import view_as_blocks
from scipy.spatial import cKDTree
from scipy.stats import circmean

def rotate_coords(x_i,y_i,x_p,y_p,theta):
    '''Rotate coordinates (xi,yi) theta degrees around point (xp,yp)
    '''
    theta = np.radians(theta)
    x_r = x_p + ((x_i-x_p)*np.cos(theta)) - ((y_i-y_p)*np.sin(theta))
    y_r = y_p + ((x_i-x_p)*np.sin(theta)) + ((y_i-y_p)*np.cos(theta))
    return x_r,y_r

def main():
    ''' Perform a two-step spatial resampling to . First, pixels are aggregated and
    averaged, next a nearest neighbor algorithm is used to resample images to resolution.
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('in_file', type=str,
                        help='Input image')
    parser.add_argument('out_dir', type=str,
                         help='Output directory')
    parser.add_argument('--pixel', type=int,default = 30,
                        help='Pixel size in map units')
    parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()
    out_pixel = args.pixel

    out_image = args.out_dir + '/' + os.path.basename(args.in_file)
    image = htl.HyTools()
    image.read_file(args.in_file,'envi')

    x_ul = float(image.map_info[3])
    y_ul = float(image.map_info[4])
    pixel_res = float(image.map_info[5])

    if 'rotation' in image.map_info[-1]:
        rotation = 360 + float(image.map_info[-1].split('=')[-1])
    else:
        rotation = 0

    # Calculate rotated and unrotated coords
    y_ind,x_ind = np.indices((image.lines,image.columns))
    y_rcoord = y_ul - y_ind*pixel_res
    x_rcoord = x_ul + x_ind*pixel_res
    if rotation != 0:
        x_coord,y_coord = rotate_coords(x_rcoord,y_rcoord,x_ul,y_ul,rotation)
    else:
        x_coord,y_coord = x_rcoord,y_rcoord

    bin_size = int(np.round(out_pixel/pixel_res))
    if args.verbose:
        print("Aggregating every %s pixels" % bin_size)

    lines =bin_size*(image.lines//bin_size)
    columns =bin_size*(image.columns//bin_size)

    y_coord_bin = np.nanmean(view_as_blocks(y_coord[:lines,:columns],
                                     (bin_size,bin_size)),axis=(2,3))
    x_coord_bin= np.nanmean(view_as_blocks(x_coord[:lines,:columns],
                                     (bin_size,bin_size)),axis=(2,3))

    # Get extent of output array
    xmax = int(out_pixel * (x_coord_bin.max()//out_pixel)) + out_pixel
    ymax = int(out_pixel * (y_coord_bin.max()//out_pixel)) + out_pixel
    xmin = int(out_pixel * (x_coord_bin.min()//out_pixel)) - out_pixel
    ymin = int(out_pixel * (y_coord_bin.min()//out_pixel)) - out_pixel

    out_columns = int((xmax-xmin)/out_pixel)
    out_lines =  int((ymax-ymin)/out_pixel)

    #Calculate coordinates of output array
    image_shape = (out_lines,out_columns)
    y_coord_out,x_coord_out = np.indices(image_shape)*out_pixel
    y_coord_out = ymax -  y_coord_out
    x_coord_out = xmin + x_coord_out

    #Create tree to convert pixels to geolocated pixels
    src_points =np.concatenate([np.expand_dims(x_coord_bin.flatten(),axis=1),
                                np.expand_dims(y_coord_bin.flatten(),axis=1)],axis=1)
    tree = cKDTree(src_points,balanced_tree= True)

    dst_points = np.concatenate([np.expand_dims(x_coord_out.flatten(),axis=1),
                                 np.expand_dims(y_coord_out.flatten(),axis=1)],axis=1)

    dists, indexes = tree.query(dst_points,k=1)
    indices_int = np.unravel_index(indexes,x_coord_bin.shape)
    mask = dists.reshape(image_shape) >out_pixel

    out_header = image.get_header()
    out_header['lines'] = out_lines
    out_header['samples'] = out_columns
    out_header['map info'][3] = str(xmin)
    out_header['map info'][4] = str(ymax)
    out_header['map info'][5:7] = out_pixel,out_pixel
    out_header['map info'][-1] ='rotation=0.0000'
    out_header['byte order'] = 0
    out_header['data ignore value'] = image.no_data

    writer = WriteENVI(out_image,out_header)
    iterator =image.iterate(by = 'band')

    while not iterator.complete:
        if args.verbose &  (iterator.current_band%10 == 0):
            print("%s/%s" % (iterator.current_band,image.bands))
        band = np.copy(iterator.read_next()).astype(float)
        band[~image.mask['no_data']] = np.nan
        bins  = view_as_blocks(band[:lines,:columns],(bin_size,bin_size))

        if (iterator.current_band in [1,3,7]) and ('obs' in image.base_name):
            bins = np.radians(bins)
            band = circmean(bins,axis=2,nan_policy = 'omit')
            band = circmean(band,axis=2,nan_policy = 'omit')
            band = np.degrees(band)
        else:
            band = np.nanmean(bins,axis=(2,3))

        band = band[indices_int[0],indices_int[1]].reshape(image_shape)
        band[mask]= image.no_data
        band[np.isnan(band)]= image.no_data
        writer.write_band(band,iterator.current_band)


if __name__ == "__main__":
    main()
