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
from scipy.interpolate import interp1d
from skimage.util import view_as_blocks

def progbar(curr, total, full_progbar = 100):
    '''Display progress bar.
    Gist from:
    https://gist.github.com/marzukr/3ca9e0a1b5881597ce0bcb7fb0adc549

    Args:
        curr (int, float): Current task level.
        total (int, float): Task level at completion.
        full_progbar (TYPE): Defaults to 100.
    Returns:
        None.
    '''
    frac = curr/total
    filled_progbar = round(frac*full_progbar)
    print('\r', '#'*filled_progbar + '-'*(full_progbar-filled_progbar), '[{:>7.2%}]'.format(frac), end='')

def main():
    ''' Perform a two-step spectral resampling to 10nm. First wavelengths are aggregated
    to approximateley 10nm, then aggregated spectra a interpolated to exactly 10nm using a
    piecewise interpolator.
    '''

    parser = argparse.ArgumentParser()
    parser.add_argument('in_file', type=str,
                        help='Input image')
    parser.add_argument('out_dir', type=str,
                         help='Output directory')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--waves',type=str,
                        default='auto')
    parser.add_argument('--kind',type=str, default='cubic',
                        help='Interpolation type')
    args = parser.parse_args()

    out_image = args.out_dir + '/' + os.path.basename(args.in_file)
    image = htl.HyTools()
    image.read_file(args.in_file,'envi')

    if args.waves == 'auto':
        if image.wavelengths.max()< 1100:
            new_waves = np.arange(400,991,10)
        else:
            new_waves = np.arange(400,2501,10)
    else:
        start,end,spacing = [int(c) for c in args.waves.split('_')]
        new_waves = np.arange(start,end+1,spacing)

    bins = int(np.round(10/np.diff(image.wavelengths).mean()))
    agg_waves  = np.nanmean(view_as_blocks(image.wavelengths[:(image.bands//bins) * bins],
                                           (bins,)),axis=1)
    agg_fwhm  = np.nanmean(view_as_blocks(image.fwhm[:(image.bands//bins) * bins],
                                           (bins,)),axis=1)

    print(image.base_name)
    print("Aggregating every %s bands" % bins)

    out_header = image.get_header()
    out_header['bands'] = len(new_waves)
    out_header['wavelength'] = new_waves.tolist()
    out_header['fwhm'] = agg_fwhm.tolist()
    out_header['default bands'] = []

    writer = WriteENVI(out_image,out_header)
    iterator =image.iterate(by = 'line')

    while not iterator.complete:
        line = iterator.read_next()[:,:(image.bands//bins) * bins]
        line  = np.nanmean(view_as_blocks(line,(1,bins,)),axis=(2,3))
        interpolator = interp1d(agg_waves,line,fill_value = 'extrapolate', kind = args.kind)
        line = interpolator(new_waves)
        writer.write_line(line,iterator.current_line)
        if args.verbose:
            progbar(iterator.current_line,image.lines, full_progbar = 100)

if __name__ == "__main__":
    main()
