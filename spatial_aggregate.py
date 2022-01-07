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
import hytools_lite as htl
from hytools_lite.io.envi import WriteENVI
import numpy as np
from skimage.util import view_as_blocks


def main():
    ''' Perform simple aggregation and averaging.
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('in_file', type=str,
                        help='Input image')
    parser.add_argument('out_dir', type=str,
                         help='Output directory')
    parser.add_argument('--mask', default = False,
                        help='Input image')
    parser.add_argument('--agg', type=int,default = 3,
                        help='Pixels to aggregate (n x n)')
    parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()

    image = htl.HyTools()
    image.read_file(args.in_file,'envi')

    if args.mask:
        mask = htl.HyTools()
        mask.read_file(args.mask,'envi')
        msk = mask.get_band(0) == 1

    out_header = image.get_header()
    out_file = args.out_dir + '/' + image.base_name + "_%spx" % args.agg
    out_header['samples'] = int(out_header['samples']/args.agg)
    out_header['lines'] = int(out_header['lines']/args.agg)
    out_header['data ignore value'] = -9999

    writer = WriteENVI(out_file,out_header)

    for band_num in range(image.bands):
        band = np.copy(image.get_band(band_num))
        if mask:
            band[msk] = np.nan
        band = np.mean(view_as_blocks(band,
                             (args.agg,args.agg)),axis=(2,3))
        band[np.isnan(band)] = -9999
        writer.write_band(band,band_num)

if __name__ == "__main__":
    main()
