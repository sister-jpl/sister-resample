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

def rotate_coords(x_i,y_i,x_p,y_p,theta):
    '''Rotate coordinates (xi,yi) theta degrees around point (xp,yp)
    '''
    theta = np.radians(theta)
    x_r = x_p + ((x_i-x_p)*np.cos(theta)) - ((y_i-y_p)*np.sin(theta))
    y_r = y_p + ((x_i-x_p)*np.sin(theta)) + ((y_i-y_p)*np.cos(theta))
    return x_r,y_r

def main():
    ''' Perform a two-step spectral resampling to 10nm. First wavelengths are aggregated
    to approximatley 10nm, then aggregated spectra a interpolated to exactly 10nm using a
    cubic piecewise interpolator.
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('in_file', type=str)
    parser.add_argument('out_dir', type=str)
    parser.add_argument('--pixel', type=int,default = 30)
    parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()
    out_pixel = args.pixel

    out_image = args.out_dir + '/' + os.path.basename(args.in_file) + "_%02dm" % args.pixel
    hy_obj = htl.HyTools()
    hy_obj.read_file(args.in_file,'envi')

    x_ul = float(hy_obj.map_info[3])
    y_ul = float(hy_obj.map_info[4])
    pixel_res = float(hy_obj.map_info[5])

    if 'rotation' in hy_obj.map_info[-1]:
        rotation = 360 + float(hy_obj.map_info[-1].split('=')[-1])
    else:
        rotation = 0

    # Calculate rotated and unrotated coords
    y_ind,x_ind = np.indices((hy_obj.lines,hy_obj.columns))
    y_rcoord = y_ul - y_ind*pixel_res
    x_rcoord = x_ul + x_ind*pixel_res
    if rotation != 0:
        x_coord,y_coord = rotate_coords(x_rcoord,y_rcoord,x_ul,y_ul,rotation)
    else:
        x_coord,y_coord = x_rcoord,y_rcoord

    bins = int(np.round(out_pixel/pixel_res))
    if args.verbose:
        print("Aggregating every %s pixels" % bins)

    lines =bins*(hy_obj.lines//bins)
    columns =bins*(hy_obj.columns//bins)

    y_coord_bin = np.nanmean(view_as_blocks(y_coord[:lines,:columns],
                                     (bins,bins)),axis=(2,3))
    x_coord_bin= np.nanmean(view_as_blocks(x_coord[:lines,:columns],
                                     (bins,bins)),axis=(2,3))

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

    out_header = hy_obj.get_header()
    out_header['lines'] = out_lines
    out_header['samples'] = out_columns
    out_header['map info'][3] = str(xmin)
    out_header['map info'][4] = str(ymax)
    out_header['map info'][5:7] = out_pixel,out_pixel
    out_header['map info'][-1] ='rotation=0.0000'
    out_header['byte order'] = 0
    out_header['data ignore value'] = hy_obj.no_data

    writer = WriteENVI(out_image,out_header)
    iterator =hy_obj.iterate(by = 'band')

    while not iterator.complete:
        if args.verbose &  (iterator.current_band%10 == 0):
            print("%s/%s" % (iterator.current_band,hy_obj.bands))
        band = np.copy(iterator.read_next()).astype(float)
        band[~hy_obj.mask['no_data']] = np.nan
        band = np.nanmean(view_as_blocks(band[:lines,:columns],
                                     (bins,bins)),axis=(2,3))
        band = band[indices_int[0],indices_int[1]].reshape(image_shape)
        band[mask]= hy_obj.no_data
        band[np.isnan(band)]= hy_obj.no_data
        writer.write_band(band,iterator.current_band)


if __name__ == "__main__":
    main()
